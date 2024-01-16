# import needed, c.f. https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#sqlmodel-metadata-order-matters
# import here all models for which we can to create tables.
from sqlmodel import SQLModel  # noqa: F401

from power_stash.inputs.entsoe.models import EntsoeConsumption
from power_stash.models.storage.database import BaseTableModel  # noqa: F401

# Add in the list all models for which we want to create hypertables for
hypter_tables = [
    (EntsoeConsumption, "timestamp"),
]
