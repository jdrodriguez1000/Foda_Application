El flujo de trabajo esperado que queremos obtener con la aplicacion es donde el trabajo del cientifico de datos pase de ser de ejecucion y logica manual, a ser de revisor y aprobador de las predicciones generadas por la aplicacion. Esto logrará que entre el 85% y el 95% del trabajo sea realizado por la aplicacion a traves de agentes de IA y el 5% al 15% restante sea realizado por el cientifico de datos.

El flujo esperado será:
1. Flujo discovery: 
    a. Definir el problema del cliente: 
        i. Consiste en entrevitar a minimo tres stakeholders de la empresa ABC para que nos explicque la situacion actual del problema que tiene el cliente. Para esto nuestro cientifico de datos lleva un cuestrionario estandarizado. Es importante que los tres stakeholders sean de areas diferentes, por ejemplo: 
            - Area de planeacion
            - Area de comercializacion
            - Area de logistica
    b. Con la informacion anterior, del cuestionario buscamos que un agente de IA, escriba un documento sobre la problematica actual de la empresa. Este documento servira para que el cientifico de datos tenga un contexto claro de la situacion actual del cliente. Ademas, este documento servira para que el cliente tenga un documento claro de la situacion actual de su problema y pueda compartirlo con otros stakeholders de la empresa. 
    c. Una vez qeu conocemos el problema de la empresa y lo que pretende solucionar, el cientifico de datos se reune con el area de sistemas de la empresa, para entender la estructura de datos que tiene la empresa. Ademas, debe comprender desde cuando tienen informacion, el estado general de esa informacion si es confiable, como se podria acceder a esa informacion. Para esto utiliza tambien un cuestionario.
    d. Con la informacion anterior, buscamos que un agente de IA, escriba un documento sobre la estructura de datos de la empresa. Este documento servira para que el cientifico de datos tenga un contexto claro de la estructura de datos de la empresa. Ademas, este documento servira para que el cliente tenga un documento claro de la estructura de datos de su empresa y pueda compartirlo con otros stakeholders de la empresa. 

    Es importante en esta etapa determinar cual ha sido el comportamiento de la empresa por diferentes factores, por ejemplo su demanda aumenta cuando hay dias festivos, disminuye en epocas festivas como Navidad, si el clima es un factor importante en la demanda de sus productos, si las promociones tienen un impacto significativo en la demanda, etc.  
    
    Como resultado final de la etapa de onboarding, esperamos qeu un agente de IA construya un archivo yaml llamado client_register.yaml donde se registre la situacion actual de la empresa, otro archivo llamado business_hypothesis.md donde se registren las hipotesis de comportamiento de la empresa y otro documento llamado contract_data.json que será el contrato de datos entre Sabbia Solution & Services y la empresa ABC. 


2. Flujo Onboarding:
    a. Con este flujo buscamos mapear la estructura de datos de la empresa en nuestro sistema, esperamos qeu esto lo realice un agente de IA, basado en el documento contract_data.json.
    b. Si el contract_data.json informa que el cliente va a enviar X archivos con informacion historica, el agente de IA debe mapear este numero exacto de archivos, esto se hace para que el cliente sepa que archivos debe enviar y de esa manera no envie informacion incompleta o adicional. 
    b. Entre otras cosas, debemos definir los parametros de la empresa:
        i. Familia
        ii. Categoria
        iii. Subcategoria
        iv. Clase
    c. Debe tambien identificar la geografia de su centros de distribucion, es decir.
        i. Region
        ii. Pais
        iii. Ciudad
        iv. Sede (sucursal/oficina/centro de despacho)
    d. En general debe construir un map_client_data.json con todo lo necesario para mapear la estructura de datos de la empresa en nuestro sistema.
    

3. Flujo Ingestion: 
    a. Consiste en cargar la informacion del cliente en el sistema, este debe ser un proceso realizado por un agente de IA.
    b. El agente de IA debe estar en la capacidad de leer el archivo contract_data.json y el map_client_data.json, estos archivos le diran a traves de que medio se debe obtener la informacion historica de la empresa. Por ejemplo, contract_data.json puede indicar que el cliente va a enviar X archivos con informacion historica, y map_client_data.json le dira a traves de que medio se debe obtener la informacion historica, por ejemplo, se debe obtener a traves de un archivo csv, o a traves de una base de datos o a traves de un API de un sistema externo. 
    c. El agente reaalizara una carga de la informacion e inmediatamente deberá comparar esa informacion con la informacion que se tiene registrada en el archivo client_register.json, de existir inconsistencias, debe informar al cientifico de datos para que realice la correccion necesaria.
    d. Si la informacion es correcta, deberá realizar una copia de la informacion y guardala en una copia bronze, esa informacion es inalterable por la empresa Sabbia Solutions & Services. 
    e. Debera informar que la informacion esta disponible para determinar la salud de los datos, y su posterior limpieza y transforamacion.

4. Flujo Profiling
    a. Este flujo consiste en determinar la salud de los datos del clientes e informarle por medio de un pareto los ajustes que se deben realizar a la informacion historica para que el modelo pueda realizar predicciones precisas.  
    b. El agente de IA debe identificar lo siguientes aspectos de la informacion historica:
        i. Identificar productos que tienen una periodicidad de entrega menor a la minima permitida, es decir que no se puede hacer predicciones precisas.
        ii. Información faltante.
        iii. Información duplicada.
        iv. Información inconsistente.
        v. Información desactualizada.
        vi. Información incompleta.
    c. El agente deberá calcular el indicador de salud de los datos e informarlo al cliente, este indicador debe ser un porcentaje, por ejemplo 85%. Esto quiere decir que el 85% de los datos estan bien y el 15% de los datos necesitan ser corregidos.
    d. Adicional a este porcentaje, el agente deberá entregar un informe indicando el porcentaje de afectacion de cada tipo de problema, por ejemplo:
        i. 15% de los datos estan incompletos.
        ii. 10% de los datos estan duplicados.
        iii. 5% de los datos estan inconsistentes.
        iv. 2% de los datos estan desactualizados.
        v. 1% de los datos estan desorganizados.
        vi. 0% de los datos estan desestructurados.
    e. Ademas por medio de un pareto, le informará al cliente cuales son los problemas con mayor afectacion y que deben ser solucionados para que el modelo pueda realizar mejores predicciones.
    f. Debera permitir que el cientifico de datos descargue el informe de salud de los datos en un archivo csv o excel.

5. Flujo Cleaning
    a. Este flujo consiste en limpiar la informacion historica del cliente, para esto el cientifico de datos debe construir en conjunto con el cliente un archivo llamada data_cleaner.yaml. 
    b. El archivo data_cleaner.yaml informa como se va a proceder con la limpieza de los datos, por ejemplo:
        i. Si hay un dato faltante en un campo X y este campo es numerico se imputara con la media o con la mediana.
        ii. Si hay un dato faltante en un campo X y este campo es categorico se imputara con la moda.
        iii. Si hay un dato faltante en un campo X y este campo es de fecha se imputara con la fecha mas cercana.
        iv. Si hay un dato duplicado en un campo X se eliminara el duplicado.
        v. Si hay un dato inconsistente en un campo X se eliminara el registro.
        vi. Si hay un dato desactualizado en un campo X se eliminara el registro.
        vii. Si hay un dato incompleto en un campo X se eliminara el registro.
    c. El agente de IA debe tomar como base para la limpieza de los datos el archivo data_cleaner.yaml y aplicar las reglas de limpieza al archivo historico del cliente.
    d. Como resultado de este flujo, en la capa silver debera tener la informacion limpia y lista para los siguietnes procesos.
    e. Ademas debera informar las transformaciones realizadas en un archivo json llamado data_cleaning.json. Este archivo servira como documentacion de las transformaciones realizadas y permitira replicar el proceso de limpieza en otros archivos historicos del cliente.
    f. El agente de IA debera permitir que el cientifico de datos descargue el archivo data_cleaning.json en un archivo csv o excel.

6. Flujo Derivation
   a. ESte flujo consiste en calcular la demanda historica agregada de los productos, ya sea, semanal, quincenal, mensual, bimestral, trimestral, semestral, anual, de acuerdo a lo estipulado en el archivo contract_data.json.
   b. El agente de IA debe tomar como base para la derivacion de la demanda historica el archivo data_cleaning.json y aplicar las reglas de derivacion al archivo historico del cliente.
   c. Como resultado de este flujo, en la capa gold debera tener la demanda historica de los productos para cada una de las sedes de la empresa, lista para los siguietnes procesos.
   d. Ademas debera informar las transformaciones realizadas en un archivo json llamado data_derivation.json. Este archivo servira como documentacion de las transformaciones realizadas y permitira replicar el proceso de derivacion en otros archivos historicos del cliente.
   e. El agente de IA debera permitir que el cientifico de datos descargue el archivo data_derivation.json en un archivo csv o excel.

7. Flujo Exploration
   a. Este flujo consiste en explorar la informacion historica a traves de un analisis exploratorio de datos y un analisis de hipotesis planteadas por el cientifico de datos para identificar patrones y tendencias segun la informacion entregada por el cliente. 
   b. El agente de IA debera generar un informe exploratorio en un archivo llamado exploration.json.
   c. El informe debe contener:
      i. Un resumen de la informacion historica del cliente.
      ii. Un resumen de los patrones y tendencias identificados.
      iii. Un resumen de las anomalias identificadas.
   d. El agente de IA debera permitir que el cientifico de datos descargue el archivo exploration.json en un archivo csv o excel.
   e. Despues debe validar las hipotesis del cliente segun el comportamiento de su negocio expresado en el archivo business_hypothesis.md, por ejemplo el cliente informa que el los dias festivos su demanda aumenta o que sus ventas aumentaron durante la pandemia de covid 19. El agente de IA debe validar estas hipotesis y entregar un informe al cliente indicando si estas hipotesis son correctas o no.
   f. Por ultimo el agente de IA, debe sugerir que variables nuevas propone crar para mejorar la calidad de las predicciones, para esto debe realizar un estudio de correlacion entre las variables existentes y la variable objetivo, es decir, la demanda. 
   g. Debe generar un archivo en formato yaml llamado feature_engineering.yaml con las variables nuevas propuestas. 

8. Flujo Featuring
    a. ESte flujo consiste en generar nuevas variables a partir de las variables existentes, por ejemplo, si el cliente tiene una variable de fecha, se puede generar una variable de dia de la semana, mes, año, etc.
    b. El agente de IA debe tomar como base para la derivacion de variables el archivo feature_engineering.yaml y aplicar las reglas de derivacion al archivo historico del cliente.
    c. Como resultado de este flujo, en la capa gold debera tener la informacion derivada y lista para los siguientes procesos.
    d. Ademas debera informar las transformaciones realizadas en un archivo json llamado feature_engineering.json. Este archivo servira como documentacion de las transformaciones realizadas y permitira replicar el proceso de derivacion en otros archivos historicos del cliente.
    e. El agente de IA debera permitir que el cientifico de datos descargue el archivo feature_engineering.json en un archivo csv o excel.

9. Flujo Modelling
    a. Consiste en determinar el mejor modelo de machine learning que se puede obtener para predecir la demanda de los productos del cliente, basandose en la informacion historica y las variables generadas.
    b. El agente de IA debera generar un torneo de campeones, para esto debe tomar los datos limpios de la capa gold y aplicar diferentes modelos de machine learning para predecir la demanda de los productos del cliente.
    c. El agente de IA debera generar un informe en un archivo llamado modelling.json. Este informe debera contener la siguiente informacion:
       i. Un resumen de los modelos de machine learning que se aplicaron.
       ii. Un resumen de los resultados obtenidos.
       iii. Un resumen de las variables que mejor explicaron la demanda de los productos.
    d. El agente de IA debera permitir que el cientifico de datos descargue el archivo modelling.json en un archivo csv o excel.
    e. Por ultimo sera el cientifico de datos quien determine cual es el modelo qeu se utilizará para realizar inferencias, para esto el agente de IA debera presentarle los resultados del torneo de campeones y hacer las recomendaciones pertinentes para la toma de decisiones. 
    f. Una vez seleccionado el modelo, el agente de IA debera generar un archivo en formato pkl llamado best_model.pkl, el cual será utilizado para realizar inferencias y crear las predicciones. 
    
10. Flujo inferences
    a. Este flujo consiste en realizar las predicciones basados en el modelo seleccionado y las variables generadas. 
    b. El agente de IA debera tomar como base para las inferencias el archivo best_model.pkl y las variables generadas para obtener las predicciones.
    c. Como resultado de este flujo, en la capa gold debera tener las predicciones para los productos del cliente. 
    d. Ademas debera informar las predicciones en un archivo json llamado inferences.json. Este archivo servira como documentacion de las inferencias realizadas y permitira replicar el proceso de inferencias en otros archivos historicos del cliente.
    e. El agente de IA debera permitir que el cientifico de datos descargue el archivo inferences.json en un archivo csv o excel. 

    Es importante que cada predicion se entregue con su metrica de desviacion, en este caso el MAPE (Mean Absolute Percentage Error), por ejemplo si el horizonte de prediccion es 3 meses entregara algo como:
    MES	ML Esperado	ML MAPE
    1	1062	10,20%
    2	1710	10,90%
    3	1489	11,87%
    
    Esta desviacion es muy importante por qeu es la base para el siguiente flujo simulation.  
    
10. Flujo simulation
    a. Consiste en realizar simulacion montecarlo a los resultados obtenidos en el flujo inferences, aplicando la desviacion correspondiente a cada mes, para obtener las predicciones optimistas, moderadas y pesimistas, ademas de la demanda simulada. 
    b. La simulacion tambien puede incluir otras variables como la influencia del lead time, la TRM, la inflacion de los productos, etc. Para esto el agente de IA debera tomar como base el archivo simulation.json y aplicar las reglas de simulacion al archivo historico del cliente.
    c. Como resultado de este flujo, en la capa gold debera tener la demanda simulada de los productos para cada una de las sedes de la empresa, lista para los siguientes procesos. 

    Se espera qeu en este punto la informacion sea algo como:
    MES	ML Esperado	ML MAPE	ML Desviacion	Demanda Simulada
    1	1062	10,20%	108	964
    2	1710	10,90%	186	1824
    3	1489	11,87%	177	1186
    4	2005	13,35%	268	1866
    5	1986	14,01%	278	2063
    6	1980	14,98%	297	2000
                    
                    
    MES	Optimista	Moderado	Pesimista	Inventario Seguridad
    1	1084	1207	1247	185
    2	1710	1943	1978	268
    3	1496	1705	1777	288
    4	2004	2322	2441	436
    5	2069	2392	2532	546
    6	2001	2336	2458	478
    

Flujo Scenarios (¿qué pasa si...?)
    a. Este flujo se ejecuta despues del flujo simulation y consiste en responder preguntas del tipo "¿que pasa si...?".
    b. Un agente de IA podra simular diferentes escenarios de negocio teniendo en cuenta la informacion entregada por el flujo inferences y el flujo simulation.
    c. (Por ahora solo se registra el flujo; el detalle de entradas, reglas y artefactos se definira mas adelante.)


11. Flujo Reporting
    a. Este flujo consiste en la creacion de informes de la demanda simulada de los productos, con base en los resultados obtenidos en el flujo simulation.  
    b. Se espera en esta etapa tener informacion como:
    MES	Precio unitario Venta	Costo unitario venta	Costo Seguridad	Margen Bruto Esperado	Costo Oportunidad
    1	        $ 65.300 	 $ 48.600 	 $ 9.006.240 	 $ 17.735.400 	 $ 3.094.737 
    2	 $ 65.300 	 $ 48.600 	 $ 13.011.879 	 $ 28.557.000 	 $ 4.471.160 
    3	 $ 65.300 	 $ 48.600 	 $ 14.009.360 	 $ 24.866.300 	 $ 4.813.916 
    4	 $ 65.300 	 $ 48.600 	 $ 21.207.505 	 $ 33.483.500 	 $ 7.287.352 
    5	 $ 65.300 	 $ 48.600 	 $ 26.531.754 	 $ 33.166.200 	 $ 9.116.878 
    6	 $ 65.300 	 $ 48.600 	 $ 23.214.652 	 $ 33.066.000 	 $ 7.977.051 

    c. El agente de IA debera generar un informe en un archivo llamado reporting.json. Este informe debera contener la siguiente informacion:
       i. Un resumen de los informes generados en los flujos anteriores.
       ii. Un resumen de las predicciones generadas.
       iii. Un resumen de las simulaciones realizadas.
    d. El agente de IA debera permitir que el cientifico de datos descargue el archivo reporting.json en un archivo csv o excel. 
    

12. Flujo Monitoring
    a. Este flujo consiste en monitorear la calidad de las predicciones y realizar ajustes cuando sea necesario. 
    b. El agente de IA debera tomar como base el archivo monitoring.json y aplicar las reglas de monitoreo al archivo historico del cliente.
    c. Como resultado de este flujo, en la capa gold debera tener el monitoreo de las predicciones para cada una de las sedes de la empresa.
    d. Ademas debera informar el monitoreo en un archivo json llamado monitoring.json. Este archivo servira como documentacion del monitoreo realizado y permitira replicar el proceso de monitoreo en otros archivos historicos del cliente. 
    e. El agente de IA debera permitir que el cientifico de datos descargue el archivo monitoring.json en un archivo csv o excel. 

13. Flujo Alerting
    a. Este flujo consiste en la generacion de alertas cuando las predicciones se desvian de manera significativa de la demanda real, para esto se debe comparar la demanda real con la demanda simulada y alertar al cliente cuando la desviacion sea mayor al porcentaje definido. 
    b. El agente de IA debera tomar como base el archivo alerting.json y aplicar las reglas de alerting al archivo historico del cliente. 
    


