# -*- coding: utf-8 -*-

# **Carga de archivos**


# Importando libreria y extrayendo archivo de drive
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials

# Carga de archivos de temperatura
url='https://docs.google.com/spreadsheets/d/1JR5Btkg78l4twIArPfL25KAExZg3UK47/edit?usp=share_link&ouid=103400984245047555538&rtpof=true&sd=true'
url='https://drive.google.com/uc?id=' + url.split('/')[-2]
met = pd.read_excel(url)

url='https://docs.google.com/spreadsheets/d/1sNVr1YfRNYGEDMIUN4YItXDJiYIKuNXY/edit?usp=share_link&ouid=103400984245047555538&rtpof=true&sd=true'
url='https://drive.google.com/uc?id=' + url.split('/')[-2]
temp = pd.read_excel(url)

# Cargar ventas.csv
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)
downloaded = drive.CreateFile({'id': '15tLma3iwAiIxwm3UFcxV8w_2a9S-WrIb'})
contenido = downloaded.GetContentString()
print("Descargados {} bytes".format(len(contenido)))

with open("ventas.csv", "w") as f:
  f.write(contenido)

ventas = pd.read_csv("ventas.csv", sep= ',')

"""# **Tratamiento de Tabla Ventas**"""

# Descartando columnas que no se van a utilizar
ventas2 = ventas.copy()
ventas2.drop(['local','desc_producto','desc_categoria'], axis=1, inplace=True)

# Convirtiendo a datetime las fechas
ventas2['fecha_vta'] = pd.to_datetime(ventas2['fecha_vta'])
ventas2.head()

# Filtrando bebidas
ventas3=ventas2.loc[(ventas2["desc_secciones"]=="Bebidas")]
ventas3.reset_index(inplace=True, drop=True)

# Analizando si existe NaN
count_nan = ventas3['fecha_vta'].isnull().sum()
print("Cantidad de valores nulos en fecha_vta: " + str(count_nan))

count_nan = ventas3['desc_secciones'].isnull().sum()
print("Cantidad de valores nulos en desc_secciones: " + str(count_nan))

count_nan = ventas3['desc_sub_secciones'].isnull().sum()
print("Cantidad de valores nulos en desc_sub_secciones: " + str(count_nan))

count_nan = ventas3['cantidad'].isnull().sum()
print("Cantidad de valores nulos en cantidad: " + str(count_nan))

# Analizando el rango de valores en la columna cantidad
print(ventas3.describe())

# Graficando los datos para visualizar los valores atípicos.
sns.set(rc={'figure.figsize':(11,8)})
sns.boxplot(x=ventas3["cantidad"])

print("Existen datos que podrían afectar el análisis, según nuestro criterio")

# Identificando los outliers

def find_outliers_IQR(df):
   q1=df.quantile(0.01) #Filtramos 2% de los extremos para dejar 
   q3=df.quantile(0.99) #un dataset más homogéneo
   IQR=q3-q1
   outliers = df[((df<(q1-1.5*IQR)) | (df>(q3+1.5*IQR)))]
   return outliers

outliers = find_outliers_IQR(ventas3["cantidad"])
print("Número outliers: "+ str(len(outliers)))
print("max outlier: "+ str(outliers.max()))
print("min outlier: "+ str(outliers.min()))

outliers2= outliers.index
ventas4 = ventas3.drop(index=outliers.index)
print("\n" + str(ventas4.describe()))

print("\nSe eliminaron los outliers del dataset")

# Volviendo a analizar el dataset
# Graficando los datos para visualizar los valores atípicos.
sns.set(rc={'figure.figsize':(11,8)})
sns.boxplot(x=ventas4["cantidad"])

# Eliminar los negativos en cantidad
ventas4=ventas4.loc[(ventas4["cantidad"] > 0)]

# Redondeando las cantidades al extremo más cercano
ventas4["cantidad"] = ventas4["cantidad"].round()
ventas4 = ventas4.loc[(ventas4["cantidad"] != 0)]
ventas4.head()

# Dataset sin cantidades negativas
# Graficando los datos para visualizar los valores atípicos.
sns.set(rc={'figure.figsize':(11,8)})
sns.boxplot(x=ventas4["cantidad"])

# Agrupando ventas por fecha, secciones y subsecciones
ventas5=ventas4.groupby(["fecha_vta", "desc_secciones","desc_sub_secciones"]).sum()

ventas5.plot(kind='hist',subplots=True,sharex=True,sharey=True,title='Frecuencia de días por cantidad de ventas', bins=60)
ventas5=ventas5.reset_index(drop=False)
ventas5

"""# **Tratamiento de Tabla Temperaturas**"""

temp2=temp.copy()

# Convertimos todos los datos de temperatura al tipo float64
temp2[(temp.columns[4::])]=temp2[(temp.columns[4::])].apply(pd.to_numeric,errors='coerce')

# Eliminamos y corregimos NaN
temp2=temp2.dropna(subset=['Código','Estación'])

# Llenamos los valores NaN con los valores del día anterior, sabiendo que no hay NaN en el día01
temp2=temp2.T.fillna(method="pad").T

# Agrupamos por día y hallamos el promedio de las estaciones
temp3=temp2.groupby(["Año", "Mes"]).mean()

# Creamos un dataframe nuevo con las fechas y el prom de temperatura en 2 columnas
temp4= pd.date_range(start='2021-01-01',end='2021-09-30').to_frame(name='fecha_vta').reset_index(drop=True)
temp4["Temperatura"] = 0.0

# Cargamos los valores de temperatura de cada fecha en el DF nuevo
for i in range(len(temp4)):
  temp4["Temperatura"][i] = temp3.loc[(temp4["fecha_vta"][i].year,temp4["fecha_vta"][i].month)][temp4["fecha_vta"][i].day]

# Analizamos el df creado
temp4.hist(column="Temperatura", bins=20)
plt.title("Frecuencia de días por temperatura promedio", size=20)

temp4.plot.scatter(y="Temperatura",x="fecha_vta")
plt.title("Temperatura medida por fecha", size=20)

# Desplegando los primeros 10 días
display(temp4.head(10))

# Analizando los datos
temp4.describe()

"""# Uniendo tabla de Ventas y Temperatura"""

import seaborn as sns
import matplotlib.pyplot as plt


#Relacionamos las temperaturas con las ventas
ventas_temp=ventas5.merge(temp4, how='left',on="fecha_vta")

#Correlación entre la temperatura y la venta de bebidas
print("Correlación entre la temperatura y la venta de bebidas: \n")
display(ventas_temp.corr())

#Correlación sin alcohol
print("\nCorrelación entre la temperatura y la venta de bebidas sin alcohol : \n")
display(ventas_temp.loc[(ventas_temp["desc_sub_secciones"]=="Sin Alcohol")].corr())

#Correlación con alcohol
print("\nCorrelación entre la temperatura y la venta de bebidas con alcohol: \n")
display(ventas_temp.loc[(ventas_temp["desc_sub_secciones"]=="Con Alcohol")].corr())

# Gráfico de tendencia de ventas de bebidas con alcohol y sin alconol
sns.lmplot(x='Temperatura',y='cantidad',data=ventas_temp,fit_reg=True,hue="desc_sub_secciones", height=7)
plt.title("Tendencia de ventas de bebidas con alcohol y sin alconol según temperatura", size=15)

"""Se observa mayor influencia de la temperatura en las bebidas sin alcohol

# Análisis de venta de bebidas
"""

#Analizando por días entre semana y fines de semana

#Separando por día de semana y fines de semana
ventas_temp=ventas5.merge(temp4, how='left',on="fecha_vta")

ventas_temp_finde=ventas_temp.copy().set_index("fecha_vta")
ventas_temp_finde=ventas_temp_finde[ventas_temp_finde.index.dayofweek>=5]

ventas_temp_semana=ventas_temp.copy().set_index("fecha_vta")
ventas_temp_semana=ventas_temp_semana[ventas_temp_semana.index.dayofweek<5]


#Correlación entre la temperatura y la venta de bebidas
print("Correlación entre la temperatura y la venta de bebidas, durante fin de semana (Vie-Sab-Dom): \n")
display(ventas_temp_finde.corr())

sns.lmplot(x='Temperatura',y='cantidad',data=ventas_temp_finde,fit_reg=True,hue="desc_sub_secciones", height=7)
plt.title("Tendencia de ventas de bebidas con alcohol y sin alconol en fin de semana según temperatura ")

print("\nCorrelación entre la temperatura y la venta de bebidas, durante la semana(Lun-Jue): \n")
display(ventas_temp_semana.corr())

sns.lmplot(x='Temperatura',y='cantidad',data=ventas_temp_semana,fit_reg=True,hue="desc_sub_secciones", height=7)
plt.title("Tendencia de ventas de bebidas con alcohol y sin alconol entre semana según temperatura ")

#Graficando las ventas por día de la semana
ventas_month=ventas4.set_index("fecha_vta")
ventas_month

ventas_dia=ventas_month.groupby([ventas_month.index.year,ventas_month.index.weekday]).sum()
ventas_dia.head(10)
ax = ventas_dia.plot(kind="bar")
ax.set_xticklabels(["L","M","M","J","V","S","D"])
plt.title("Ventas totales por día de la semana")

"""Gráficamente se observa mayor venta tanto en bebidas con y sin alcohol, durante el fin de semana. El impacto de la temperatura en bebidas con alcohol y sin alcohol permanece similar al análisis sin discriminar los días de la semana.

# Análisis de marcas más vendidas
"""

'''Agrupamos el dataset por marcas y fechas.
Utilizamos el dataset sin los outliers pero con los valores negativos
porque interpretamos, estos, como devoluciones'''

ventas6=ventas4.groupby(["fecha_vta", "desc_marca"]).sum()
ventas6=ventas6.reset_index()

#Contamos la frecuencia de venta de marcas
cuenta=ventas6["desc_marca"].value_counts()

#Eliminamos las marcas que tienen una frecuencia de venta menor a la media
cuenta=cuenta[cuenta>cuenta.]
venta_cuenta=ventas6.loc[ventas6["desc_marca"].isin(cuenta.index)]

#Unimos con el dataset de temperatura
marca_temp=venta_cuenta.merge(temp4, how='left',on="fecha_vta")
marca_temp=marca_temp.drop(columns="fecha_vta")

#hallamos la correlación de la venta de estas marcas con la temperatura
corr=marca_temp.groupby("desc_marca").corr()
corr=corr.reset_index()

#Filtramos las marcas que tienen una correlación absoluta importante (>0.5)
corr_05=corr[(abs(corr["cantidad"])>0.5)]
corr_05=corr_05[(abs(corr_05["cantidad"])!=1)]

#Graficamos 
sns.lmplot(x='Temperatura',y='cantidad',data=marca_temp.loc[marca_temp["desc_marca"].isin(corr_05["desc_marca"])],fit_reg=True,hue="desc_marca",height=8)
plt.title("Ventas/Temperatura")



"""**¿Cuáles son las tres marcas de bebidas de mayor venta? Demuestre la respuesta utilizando tablas y gráficos adecuados.**"""

# Primeros tres
ventas4.groupby(["desc_marca"]).sum().sort_values(by="cantidad",ascending=False).head(3)
ventas4_hist=ventas4.groupby(["desc_marca"]).sum().sort_values(by="cantidad",ascending=False).head(10)

ventas4_hist.plot(kind="bar")
plt.title("Cantidad de ventas de bebidas por marca",size=18)
ventas4_hist.head(3)

"""**¿Qué otra información relevante encuentra en el conjunto de datos?**"""

#Graficamos la frecuencia de ventas por cantidad vendida.

ventas4.hist(column="cantidad", bins=30)
plt.title("Frecuencia de ventas por cantidad vendida")

#Creamos dataset para graficar
ventas_month=ventas4.set_index("fecha_vta")
ventas_month

#Graficamos el total de ventas de bebidas por mes
ventas_mes=ventas_month.groupby(pd.Grouper(freq="M")).sum()
ventas_mes.head(10)
ventas_mes.plot(kind="line")
plt.title("Total de ventas de bebidas por mes")

#Graficamos el total de ventas de bebidas por día
ventas_dia=ventas_month.groupby(pd.Grouper(freq="D")).sum()
ventas_dia.head(10)
ventas_dia.plot(kind="line")
plt.title("Total de ventas de bebidas por día")

#Días de mayor venta
print("Los días de mayor venta son: \n")
display(ventas5.sort_values(by="cantidad", ascending=False).head(10))

#Días de menor venta
print("\nLos días de menor venta son: \n")
display(ventas5.sort_values(by="cantidad", ascending=True).head(10))

"""
*   En el 1er gráfico, se observa que la mayoría de las ventas son de 1 unidad.
*   En el segundo gráfico, se observa que el mes con menor venta fue Junio y el de mayor ventas fue Marzo.
*   En el 3er gráfico podemos ver los ciclos de ventas. Los picos corresponden a los fines de semana. 
*   Los máximos ocurridos en fecha de 2021-02-26 y 2021-04-30	corresponden a los días con mayores ventas del período analizado. Estas fechas precedieron a un feriado nacional.


"""
