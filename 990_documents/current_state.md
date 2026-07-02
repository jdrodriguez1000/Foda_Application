Actualmente mi empresa Sabbia Soluitons & Services conocida como Triple S, ofrece el servicio de Planeacion de la demanda por medio de modelos de machine learning.  

Nuestro servicio es ofrecido a traves de cientificos de datos especializados en la cadena de suministro y analitica presdictiva para obtener las mejores predicciones.

Nuestros clientes son empresas de manufactura muy diversas, por ejemplo:
1. Una empresa puede tener un solo producto y distribuye en una sola ciudad a varios clientes.
2. Una empresa puede tener varios productos y distribuyen en varias ciudadades de un pais.
3. Una empresa puede tener varios productos y distribuyen en varias ciudades y puede tener varias sedes en ese pais.
4. una empresa puede tener varios productos y distribuir sus productos en varios paises, multiples ciudades y multiples sedes.
5. En general nuestras empresas pueden clasificar sus productos en Familia, Categoria, Subcategoria. y ademas pueden distribuir por ubicacion geografica en Region - Pais - Ciudad - Sede (sucursal/oficina/centro de despacho) - Bodega.
6. Ademas, pueden distribuir sus productos por tipo de cliente, por ejemplo:
    a. Minorista
    b. Mayorista
    c. Detallista
    d. Distribuidores
    e. Tienda departamental
    f. Supermercados
7. Llamaremmos a la empresa a la que le ofrecemos nuestro servicio como empresa ABC, esta empresa produce lo productos PRD1, PRD2, PRD3,...., PRDn.
8. Esta empresa tiene centros de distribucion CD1, CD2, CD3,...., CDm, a los cuales llegan los productos desde la fabrica, y de ahi se distribuyen a los clientes.
9. Los productos PRD1, PRD2, PRD3,...., PRDn se distribuyen de la siguiente manera:
    a. Familia de productos, por ejemplo: Alimentos, Bebidas, Productos de Limpieza, ... (en general son 3 niveles de agrupacion)
    b. Categoria de productos, por ejemplo: Lacteos, Canned Foods, Snacks, etc.
    c. Subcategoria de productos, por ejemplo: Yogurts, Cheeses, Canned Tomatoes, Chips, etc.
10. Otra clasificacion que pueden tener los productos es por clase, por ejemplo:
    a. Clase A: productos con demanda alta
    b. Clase B: productos con demanda media
    c. Clase C: productos con demanda baja
11. Los centros de distribucion se clasifican de la siguiente manera:
    a. Region
    b. Pais
    c. Ciudad
    d. Sede (sucursal/oficina/centro de despacho)
    e. Bodega.
12. Llamaremos la empresa XYZ, la empresa que realiza pedidos a la empresa ABC, estos pedidos pueden variar en frecuencia, algunos los realizan para el proximo mes, para las siguientes dos semanas, otros las pueden realizr para el siguiente trimestre. En general, hay una periodicidad de entrega de los pedidos, la cual puede ser semanal, quincenal, mensual, bimestral, trimestral, semestral, anual.

Por lo tanto tenemos dos problemas en este momento:
1. Predecir la demanda de los productos PRD1, PRD2, PRD3,...., PRDn para la empresa XYZ, estos productos llegan desde un centro de distribucion CD1, CD2, CD3,...., CDm y se distribuyen a los clientes XYZ1, XYZ2, XYZ3,...., XYZk. Cada uno de estos clientes XYZj tienen differentes periodicidades de entrega. Ademas, hay diferentes tipos de clientes, por lo que no todos los clientes tienen la misma demanda.
2. Dependemos totalmente de los cientificos de datos, esto nos impide escalar nuestro negocio de manera mas rapida.
3. Buscamos una solucion automatizada para predecir la demanda de los productos para la empresa XYZ, por lo que necesitamos replicar las predicciones que realizan los cientificos de datos de nuestra empresa para la empresa XYZ, para ello necesitamos tener una representacion del negocio, una especie de gemelo digital que nos permita simular la demanda de los productos, y a partir de ahi obtener las predicciones.
4. Actualmente nuestro modelo de negocio es totalmente basado en un servicio, y nos queremos pasar a un modelo Service as a Software (SaaSw), qeu nos permita con un mismo cientifico de datos manejar varias empresas de manera automatizada y asi poder escalar.
5. Es importante que inicialmente el modelo sea SaaSw, porque nuestros clientes confian mucho en el criterio del ser humano (cientifico de datos) que lo está atendiendo, pero buscamos un esquema donde logremos automatizar entre el 85% y 95% del trabajo realizado por el cientifico de datos y el resto del trabajo lo realicemos a traves de agentes de IA especializados.
6. Es muy importante y se debe tener claro qeu predecimos la demanda de sus productos, no predecimos las ventas.

Actulamente nuestro cientificos de datos entregan la siguiente informacion a nuestros clientes:
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
                    
                    
MES	Precio unitario Venta	Costo unitario venta	Costo Seguridad	Margen Bruto Esperado	Costo Oportunidad
1	 $ 65.300 	 $ 48.600 	 $ 9.006.240 	 $ 17.735.400 	 $ 3.094.737 
2	 $ 65.300 	 $ 48.600 	 $ 13.011.879 	 $ 28.557.000 	 $ 4.471.160 
3	 $ 65.300 	 $ 48.600 	 $ 14.009.360 	 $ 24.866.300 	 $ 4.813.916 
4	 $ 65.300 	 $ 48.600 	 $ 21.207.505 	 $ 33.483.500 	 $ 7.287.352 
5	 $ 65.300 	 $ 48.600 	 $ 26.531.754 	 $ 33.166.200 	 $ 9.116.878 
6	 $ 65.300 	 $ 48.600 	 $ 23.214.652 	 $ 33.066.000 	 $ 7.977.051 


En estos momentos, nuestro equipo de científicos de datos se encuentra generando estas tablas para el cliente. Pero necesitamos crear una herramienta que permita generar estas tablas de manera automatizada, replicando la lógica que utilizan actualmente los científicos de datos.  

Lo mas importante es que el modelo que se cree permita escalar, es decir, que podamos agregar nuevos productos y nuevas sedes de manera sencilla.  

El flujo actual de trabajo de nuestros cientificos de datos es:
1. Cliente Nuevo: Una vez el equipo comercial informa que tenemos un cliente nuevo, asignamos un cientifico de datos para iniciar lo que conocemos como el proyecto, que va desde el registro del cliente hasta obtener su primera prediccion. El flujo que sigue es el siguiente:
   1. Se registra el cliente en nuestra plataforma
   2. Se recopila la informacion historica de ventas del cliente. 
   3. Se clasifica los productos del cliente en familias, categorias, subcategorias.
   4. Se crea la estructura para recibir los datos de los pedidos, por ejemplo, si el cliente tiene 5 sedes, se crean 5 estructuras para recibir los datos de los pedidos, cada una de ellas con sus 6 productos. Y ademas se crean 5 estructuras para el inventario, una por cada sede. y una estructura para los precios, una por cada sede.
   5. Se carga la informacion historica de ventas del cliente.   
   6. Se ejecuta el modelo de prediccion de demanda para los productos del cliente, este modelo se ejecuta a traves de script que se ejecutan en una terminal. Y se obtienen las tablas para optimista, moderado y pesimista. Ademas de la desviacion estandar. 
   7. Una vez se obtiene las tablas, se genera el informe para el cliente con el precio de venta, costo unitario de venta, costo de inventario, margen bruto esperado y costo de oportunidad. 
   8. El cliente puede revisar el informe y si esta de acuerdo con la prediccion, se genera el informe final y se envia al cliente.   
   
2. Cliente Recurrente: Este es un cliente qeu mes a mes enviamos la prediccion de la demanda de sus productos, para ello 
   1. Algunos clientes nos envian sus pedidos por correo electronico, otros nos envian sus pedidos a traves de un portal web, o nos envian un archivo plano con la informacion.  
   2. El cientifico de datos procesa, limpia esa informacion, y la carga en la estructura que ya tiene creada para el cliente. 
   3. Una vez se carga la informacion, se ejecuta el modelo de prediccion de demanda para los productos del cliente, este modelo se ejecuta a traves de script que se ejecutan en una terminal. Y se obtienen las tablas para optimista, moderado y pesimista. Ademas de la desviacion estandar. 
   4. Una vez se obtiene las tablas, se genera el informe para el cliente con el precio de venta, costo unitario de venta, costo de inventario, margen bruto esperado y costo de oportunidad. 
   5. El cliente puede revisar el informe y si esta de acuerdo con la prediccion, se genera el informe final y se envia al cliente.   

Este flujo de trabajo actual, hace qeu dependamos mucho del conocimiento del cientifico de datos que atiende el cliente, y no nos permite escalar de manera rapida, ya que cada cientifico de datos solo puede atender a un numero muy limitado de clientes (maximo 4). Por esta razon, estamos buscando una solucion automatizada para predecir la demanda de los productos para la empresa XYZ, por lo que necesitamos replicar las predicciones que realizan los cientificos de datos de nuestra empresa para la empresa XYZ, para ello necesitamos tener una representacion del negocio, una especie de gemelo digital que nos permita simular la demanda de los productos, y a partir de ahi obtener las predicciones.