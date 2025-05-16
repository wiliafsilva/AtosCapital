# Importação completa do módulo 'consultaSQL'
import consulta_SQL_mes

# Obtendo os nomes das filiais
filiais = consulta_SQL_mes.obter_nmfilial()
print("Filiais encontradas:", filiais)

# Obtendo o total de vendas para uma filial
total_vendas = consulta_SQL_mes.obter_vendas_ano_anterior_mes_anterior('FILIAL 0001')
print("Total de vendas para a filial 'FILIAL 0001' em março de 2024:", total_vendas)

# Obtendo a meta de vendas
meta_mes = consulta_SQL_mes.obter_meta_mes_anterior('FILIAL 0001') 
print(f"Meta de vendas para a filial 'FILIAL 0001' em março de 2024 (com 5% de acréscimo): {meta_mes}")

previsao = consulta_SQL_mes.obter_previsao_vendas('FILIAL 0001')
print(f"Previsão de vendas para a filial 'FILIAL 0001': {previsao}")

acumulo_vendas_ano_anterior = consulta_SQL_mes.acumulo_vendas_periodo_ano_anterior('FILIAL 0001')
print("Acumulo de vendas da filial 'FILIAL 0001' no mesmo período do ano anterior:", acumulo_vendas_ano_anterior)

acumulo_meta_ano_anterior = consulta_SQL_mes.obter_acumulo_meta_ano_anterior('FILIAL 0001')
print("Acumulo de meta de vendas da filial 'FILIAL 0001' no mesmo período do ano anterior:", acumulo_meta_ano_anterior)

acumulo_de_vendas = consulta_SQL_mes.obter_acumulo_de_vendas('FILIAL 0001')
print("Acumulo de vendas da filial 'FILIAL 0001' no mês atual:", acumulo_de_vendas)

vendas_dia_anterior = consulta_SQL_mes.obter_ultima_venda_com_valor('FILIAL 0001')
print("Vendas do dia anterior da filial 'FILIAL 0001':", vendas_dia_anterior)

percentual_crescimento_atual = consulta_SQL_mes.obter_percentual_de_crescimento_atual('FILIAL 0001')
print("Percentual de crescimento atual da filial 'FILIAL 0001':", percentual_crescimento_atual)

percentual_crescimento_meta = consulta_SQL_mes.obter_percentual_crescimento_meta('FILIAL 0001')
print("Percentual de crescimento meta da filial 'FILIAL 0001':", percentual_crescimento_meta)

vendas_mensais = consulta_SQL_mes.obter_vendas_anual_e_filial_mes_anterior('FILIAL BELÉM')
print(vendas_mensais)
