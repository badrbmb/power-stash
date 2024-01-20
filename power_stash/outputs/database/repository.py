from typing import Any, Optional, Sequence, Type

import pandas as pd
import structlog
from pandas.core.api import DataFrame as DataFrame
from sqlalchemy import text
from sqlalchemy.exc import NotSupportedError
from sqlmodel import Session, create_engine, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from power_stash.models.storage.database import DatabaseRepository
from power_stash.outputs.database.config import DatabaseSettings
from power_stash.outputs.database.tables import BaseTableModel, SQLModel, hypter_tables

logger = structlog.get_logger()


class SqlRepository(DatabaseRepository):
    def __init__(self, init_db: bool = False) -> None:
        self.db_settings = DatabaseSettings()  # type: ignore
        self.engine = create_engine(self.db_settings.connection, echo=False)
        if init_db:
            self.init_db()
        self.tables = self.list_tables()

    @staticmethod
    def create_hypertable(session: Session, model: BaseTableModel, time_column_name: str) -> None:
        """Create a TimeScale hyptertable for the selected model with the defined time_column.

        Note: Make sure the time_column_name is a primary key for the chosen table...
        """
        table_name = model.__tablename__
        create_hypertable_query = """
        SELECT create_hypertable(:table_name, by_range(:time_column_name), if_not_exists => TRUE);
        """

        try:
            session.exec(
                statement=text(create_hypertable_query),  # type: ignore
                params={"table_name": table_name, "time_column_name": time_column_name},
            )  # type: ignore
            session.commit()
        except NotSupportedError as e:
            session.rollback()
            # hypertable might be full, cannot create hypertable in that case
            if "not empty" not in str(e):
                raise

    def init_db(self) -> None:
        """Create all tables."""
        SQLModel.metadata.create_all(bind=self.engine, checkfirst=True)
        with Session(self.engine) as session:
            for model, time_column_name in hypter_tables:
                self.create_hypertable(session, model, time_column_name)
        logger.debug(
            event="Init SQL repository.",
            db_settings=self.db_settings,
            tables=self.tables,
        )

    def exists(self, *, record: BaseTableModel) -> bool:
        """Check if the record already exists in database."""
        record_model = type(record)
        with Session(self.engine) as session:
            statement = select(record_model.uid).where(record_model.uid == record.uid)
            result = session.exec(statement).first()
            return result is not None

    @staticmethod
    def list_tables() -> list[str]:
        """List all tables."""
        return [t.name for t in SQLModel.metadata.sorted_tables]

    def drop_tables(self) -> None:
        """Drop all tables."""
        BaseTableModel.metadata.drop_all(bind=self.engine)

    def add(self, *, record: BaseTableModel) -> bool:
        """Add record."""
        with Session(self.engine) as session:
            session.add(record)
            session.commit()
        return True

    def add_or_update(self, *, record: BaseTableModel) -> bool:
        """Add or update record."""
        with Session(self.engine) as session:
            existing_record = session.get(type(record), record.uid)
            if existing_record:
                for field, value in record.model_dump().items():
                    if field != "uid":
                        setattr(existing_record, field, value)
                session.commit()
            else:
                session.add(record)
                session.commit()
        return True

    def _get_existing_records_uids(
        self,
        model_type: BaseTableModel,
    ) -> Sequence[str]:
        with Session(self.engine) as session:
            statement = select(model_type.uid)
            result = session.exec(statement)
            return result.fetchall()

    def bulk_add(
        self,
        *,
        records: list[BaseTableModel],
    ) -> bool:
        """Bulk add records, with update logic."""
        if not records:
            return False

        # get SQLModel class
        model_type = type(records[0])

        # remove existing records
        existing_uids = self._get_existing_records_uids(
            model_type=model_type,
        )
        new_records = [t for t in records if t.uid not in existing_uids]

        # store all new records
        with Session(self.engine) as session:
            try:
                with session.begin():
                    session.bulk_save_objects(new_records)
            except Exception as e:
                session.rollback()
                raise e
            else:
                session.commit()

        logger.debug(
            event="Bulk add records successful!",
            destination_table=model_type.__name__,
            count_new_records=len(new_records),
            count_requested_records=len(records),
        )
        return True

    def get(
        self,
        *,
        record_type: Type[BaseTableModel],
        record_uid: str,
    ) -> Optional[BaseTableModel]:
        """Get a record by uid."""
        with Session(self.engine) as session:
            return session.get(record_type, record_uid)

    def query(
        self,
        *,
        statement: Select | SelectOfScalar,
        return_df: bool = True,
    ) -> Sequence[BaseTableModel | Any] | pd.DataFrame:
        """Query based on select statement."""
        if not return_df:
            with Session(self.engine) as session:
                results = session.exec(statement)
                return results.fetchall()
        else:
            return pd.read_sql(sql=statement, con=self.engine)
