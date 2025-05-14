from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama
from langchain.agents.agent_types import AgentType

# Connexion à la base
db = SQLDatabase.from_uri("sqlite:///data/garmin_data.db")

# Utilisation de LLaMA 3 avec Ollama
llm = ChatOllama(model="llama3")

# Toolkit et agent
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True  # Toujours utile avec Ollama
)

# Requête test
response = agent_executor.invoke("Quel est le temps de course estimé sur un 10 km pour l'utilisateur 1 ?")
print("\n🦙 Réponse de l'agent LLaMA 3 :", response)
