import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent

from langchain.sql_database import SQLDatabase
#SQLAlchemy wrapper around a database.

from langchain.agents.agent_types import AgentType
#an Enum for agent types... what is enum??

from langchain.callbacks import StreamlitCallbackHandler
#This CallbackHandler is geared towards use with a 
#LangChain Agent; it displays the Agent's LLM and tool-usage "thoughts" 
#inside a series of Streamlit expanders.

from langchain.agents.agent_toolkits import SQLDatabaseToolkit 
#SQLDatabaseToolkit for interacting with SQL databases.

from sqlalchemy import create_engine
# SQL alchemy will actually help you to map 
# with respect to the output that is specifically coming from your
# SQL database

import sqlite3
from langchain_groq import ChatGroq

st.set_page_config(page_title="LangChain Talk With Your DB", page_icon="🗣️")
st.title("LangChain and SQL: Talk with your Database")

#INJECTION_WARNING= 
#"""
#QL agent can be vulnerable to prompt injection. 
#Use a DB role with limited permissions. 
#Read more [here](https://python.langchain.com/docs/security)
#"""

#"""
#When using LLMs (like ChatGPT) to convert natural language into SQL queries,
#prompt injection is a security risk where a malicious user injects harmful input into
#the chat prompt that causes the LLM to generate dangerous or unintended SQL.
#If a user types:
#"Show all users; DROP TABLE users;"
#The LLM might generate and run:
#SELECT * FROM users; DROP TABLE users; which is a security risk
#"""
# Two global variables
LOCALDB = "USE_LOCALDB"
MYSQL = "USE_MYSQL"

# Radio Options
radio_opt = ["Use SQLLite 3 database- Student.db","Connect to your own SQL Database"]

# "Radio operations" usually refer to how radio buttons 
# (single-choice selectors) work in user interfaces.

selected_op = st.sidebar.radio(label = "Choose the DB which you want to chat with",options = radio_opt)

if radio_opt.index(selected_op)==1: # Connecting to the MYSQL Workbench
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input("Provide mysql hostname")
    mysql_user = st.sidebar.text_input("What is the MYSQL Username")
    mysql_pass = st.sidebar.text_input("Enter your Host Password", type = "password")
    mysql_db =  st.sidebar.text_input("MySQL Database") # user needs to provide from the application itself
else:
    db_uri = LOCALDB

api_key = st.sidebar.text_input(label = "Groq API KEY",type = "password")

if not db_uri:
    st.info("Please enter the db information")

if not api_key:
    st.info("Please enter the GROQ Api key")

# LLM MODELLING

llm = ChatGroq(api_key=api_key,model="Llama3-8b-8192",streaming=True)

# CONFIGURING THE DATABASE BASED ON THE INPUT PROVIDED
@st.cache_resource(ttl ="2h") # decorator (caches our mysql)
def configure_db(db_uri,mysql_host=None,mysql_user=None,mysql_pass=None,mysql_db=None):
    if db_uri == LOCALDB:
        db_file_path = (Path(__file__).parent/"student.db").absolute()
        print(db_file_path)

        # We will connect to sql using sqlite3.connect function in read only mode 
        # cuz chatbot should only read bnut not modify the data.
        # Then returning the sqlDatabase which is gonna be engine inside
        # SQLDatabase is a LangChain wrapper to help the LLM understand your database's structure.
        #  create_engine(..., creator=...) lets you plug in your custom SQLite connection
        # This setup is then passed to an SQL agent (usually built with LangChain) that takes user questions, converts them into SQL, and fetches results.
        creator = lambda: sqlite3.connect(f"file:{db_file_path}?mode=ro",uri=True)
        return SQLDatabase(create_engine("sqlite:///",creator = creator))
    elif db_uri == MYSQL:
        if not (mysql_host and mysql_user and mysql_pass and mysql_db):
            st.error("please provfide all MYSQL connection details")
            st.stop()
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_pass}@{mysql_host}/{mysql_db}"))
if db_uri == MYSQL:
    db = configure_db(db_uri,mysql_host,mysql_user,mysql_pass,mysql_db)
else: 
    db = configure_db(db_uri)


# I'll say, hey, please display the records of, uh, all the records in the student table.

# Then it should.

# This LLM model will probably create a query for us.

# And then with the help of that particular query, we will try to interact with this.
# That work is done by the toolkit.


# CREATING TOOLKIT NOW
toolkit = SQLDatabaseToolkit(db = db, llm=llm)
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose = True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

if "messages" not in st.session_state or st.sidebar.button("Clear Message History"):
    st.session_state["messages"] = [{"role":"assistant","content":"hello User, I'm an SQL Agent how can I help you?"}]
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg['content'])
    # a message comes in st, as a format of chat
    # whose sender is given as msg['role']
    # and the content is given inside as write(msg['content])
user_query = st.chat_input(placeholder="Ask anything you need from database")

if user_query:
    st.session_state.messages.append({'role':'user','content':user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        streamlit_callback = StreamlitCallbackHandler(st.container())
        response = agent.run(user_query,callbacks=[streamlit_callback])
        st.session_state.messages.append({"role":"assistant","content":response})
        