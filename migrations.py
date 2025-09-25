async def m001_initial(db):
    """
    Initial templates table.
    """
    await db.execute(
        f"""
        CREATE TABLE recurring.maintable (
            id TEXT PRIMARY KEY,
            price_id TEXT,
            payment_method_types TEXT,
            success_url TEXT,
            metadata TEXT,
            customer_email TEXT,
            check_live BOOLEAN DEFAULT TRUE,
            wallet_id TEXT,
            last_checked TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
    """
    )
