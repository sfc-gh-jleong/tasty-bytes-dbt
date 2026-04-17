select *
from {{ source('tasty_bytes_dbt_db', 'CUSTOMER_LOYALTY') }}
