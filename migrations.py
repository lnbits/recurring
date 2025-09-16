async def m001_initial(db):
    """
    Initial templates table.
    """
    await db.execute(
        """
        CREATE TABLE reccuring.maintable (
            id TEXT PRIMARY KEY,
            price_id TEXT,
            payment_method_types TEXT,
            success_url TEXT,
            metadata TEXT,
            customer_email TEXT,
            check_live BOOLEAN DEFAULT TRUE,
            wallet_id TEXT
        );
    """
    )