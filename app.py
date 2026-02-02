import os
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

import streamlit as st
from model.database import init_db
from view.trade_view import render

init_db()
render()
