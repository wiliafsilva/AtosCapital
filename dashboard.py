import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import locale as lc
import consultaSQL
import sys
from inspect import getmembers, isfunction
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
