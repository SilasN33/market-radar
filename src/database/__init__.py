from .database import (
    init_db,
    get_connection,
    upsert_product,
    save_cluster,
    get_cluster_id_by_name,
    save_opportunity,
    get_latest_ranking,
    get_db_stats,
    create_user,
    get_user_by_email,
    get_user_by_id,
    verify_password,
    get_user_saved_opportunities,
    save_opportunity_for_user,
    get_user_projects,
    create_project,
    # V2
    add_term_history_snapshot,
    get_term_history
)

# IMPORTANT: Auto-apply patches (Postgres for production)
from . import patch
