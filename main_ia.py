from query_sql_ia import generate_sql
from execute_sql import execute_sql_command
from answer_ia import generate_answer

query = str(input("Digite sua pergunta: "))

sql_command = generate_sql(query)
print(sql_command)

result = execute_sql_command(sql_command)
print(result)

answer = generate_answer(query, result)
print(answer)