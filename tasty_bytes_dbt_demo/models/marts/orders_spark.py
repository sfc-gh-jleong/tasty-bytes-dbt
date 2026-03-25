from snowflake.snowpark.functions import col

def model(dbt, session):
    dbt.config(materialized="table")

    od = dbt.ref('raw_pos_order_detail')
    oh = dbt.ref('raw_pos_order_header')
    t = dbt.ref('raw_pos_truck')
    m = dbt.ref('raw_pos_menu')
    f = dbt.ref('raw_pos_franchise')
    l = dbt.ref('raw_pos_location')
    cl = dbt.ref('raw_customer_customer_loyalty')

    df = (
        od
        .join(oh, od["ORDER_ID"] == oh["ORDER_ID"], "inner")
        .join(t, oh["TRUCK_ID"] == t["TRUCK_ID"], "inner")
        .join(m, od["MENU_ITEM_ID"] == m["MENU_ITEM_ID"], "inner")
        .join(f, t["FRANCHISE_ID"] == f["FRANCHISE_ID"], "inner")
        .join(l, oh["LOCATION_ID"] == l["LOCATION_ID"], "inner")
        .join(cl, oh["CUSTOMER_ID"] == cl["CUSTOMER_ID"], "left")
    )

    result = df.select(
        oh["ORDER_ID"],
        oh["TRUCK_ID"],
        oh["ORDER_TS"],
        od["ORDER_DETAIL_ID"],
        od["LINE_NUMBER"],
        m["TRUCK_BRAND_NAME"],
        m["MENU_TYPE"],
        t["PRIMARY_CITY"],
        t["REGION"],
        t["COUNTRY"],
        t["FRANCHISE_FLAG"],
        t["FRANCHISE_ID"],
        f["FIRST_NAME"].alias("FRANCHISEE_FIRST_NAME"),
        f["LAST_NAME"].alias("FRANCHISEE_LAST_NAME"),
        l["LOCATION_ID"],
        cl["CUSTOMER_ID"],
        cl["FIRST_NAME"],
        cl["LAST_NAME"],
        cl["E_MAIL"],
        cl["PHONE_NUMBER"],
        cl["CHILDREN_COUNT"],
        cl["GENDER"],
        cl["MARITAL_STATUS"],
        od["MENU_ITEM_ID"],
        m["MENU_ITEM_NAME"],
        od["QUANTITY"],
        od["UNIT_PRICE"],
        od["PRICE"],
        oh["ORDER_AMOUNT"],
        oh["ORDER_TAX_AMOUNT"],
        oh["ORDER_DISCOUNT_AMOUNT"],
        oh["ORDER_TOTAL"],
    )

    return result
