from typing import Any

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
    def __init__(self) -> None:
        self.db_settings = DatabaseSettings()
        self.engine = create_engine(self.db_settings.connection, echo=False)
        self.init_db()
        self.tables = self.list_tables()
        logger.debug(
            event="Init SQL repository.",
            db_settings=self.db_settings,
            tables=self.tables,
        )

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
                statement=text(create_hypertable_query),
                params={"table_name": table_name, "time_column_name": time_column_name},
            )
        except NotSupportedError as e:
            # hypertable might be full, cannot create hypertable in that case
            if "not empty" not in str(e):
                raise

    def init_db(self) -> None:
        """Create all tables."""
        SQLModel.metadata.create_all(bind=self.engine, checkfirst=True)
        with Session(self.engine) as session:
            for model, time_column_name in hypter_tables:
                self.create_hypertable(session, model, time_column_name)

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

    def _get_existing_records_uids(
        self,
        model_type: BaseTableModel,
    ) -> list[str]:
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

        try:
            # get SQLModel class
            model_type = type(records[0])

            # remove existing records
            existing_uids = self._get_existing_records_uids(
                model_type=model_type,
            )
            new_records = [t for t in records if t.uid not in existing_uids]

            # store all new records
            with Session(self.engine) as session:
                session.bulk_save_objects(new_records)
                session.commit()

            logger.debug(
                event="Bulk add records successful!",
                count_new_records=len(new_records),
                count_requested_records=len(records),
            )
            return True
        except Exception as e:
            # TODO: remove broad expection
            logger.error(
                event="Failed to bulk add",
                error=e,
            )
            return False

    def query(
        self,
        *,
        statement: Select | SelectOfScalar,
        return_df: bool = True,
    ) -> list[BaseTableModel | Any] | pd.DataFrame:
        """Query based on select statement."""
        if not return_df:
            with Session(self.engine) as session:
                results = session.exec(statement)
                return results.fetchall()
        else:
            return pd.read_sql(sql=statement, con=self.engine)
