# 🩺 Documentación de Proceso: Análisis de Datos de Diabetes

Este documento detalla el flujo de trabajo de limpieza, transformación y enriquecimiento de datos aplicado al dataset principal `df_main`, con el objetivo de preparar la información para un análisis exploratorio (EDA) robusto y eficiente.

---

## 1. 🧹 Limpieza Inicial y Gestión de Nulos

Al explorar el dataset principal, se identificó que los valores faltantes estaban representados por el carácter `?`.

* **Estandarización:** Se convirtieron todos los valores `?` a `NaN` para permitir un análisis estadístico real del estado del dataset.
* **Gestión de Variables Categóricas:** Para conservar la utilidad de las columnas categóricas, se renombraron los valores nulos o desconocidos como `Other` en las siguientes variables:
    * **Race:** Valores `?` asignados a `Other`.
    * **Gender:** Valores `Unknown/Invalid` asignados a `Other`.
    * **Payer_code** y **Medical_speciality:** Valores `?` asignados a `Other`.
* **Eliminación de Columnas de Baja Densidad:** Se detectó que las columnas `weight` (peso), `A1Cresult` (azúcar en sangre) y `max_glu_serum` (glucosa máxima) tenían un **90% de valores nulos**. Al no ser recuperables, se eliminaron para evitar sesgos.

---

## 2. 🧩 Desafío Técnico: Estandarización CIE-9

Uno de los puntos más críticos y desafiantes del proceso fue el tratamiento de las columnas de diagnóstico (`diag_1`, `diag_2`, `diag_3`), las cuales utilizan la **Clasificación Internacional de Enfermedades (CIE-9)**.

* **Estrategia:** Se realizó una agrupación basada en los códigos médicos para identificar específicamente casos de diabetes frente a otras patologías.
* **Resultado:** Se generaron tres nuevas columnas: `diag_1_group`, `diag_2_group` y `diag_3_group`.
* **Optimización:** Tras el agrupamiento, se eliminaron las columnas originales con códigos crudos para mejorar la legibilidad y reducir el peso del dataset.

---

## 3. 💊 Estandarización de Tratamientos y Medicación

El dataset original presentaba 23 columnas individuales de medicamentos, lo que hacía el análisis tedioso. Se simplificó la lógica mediante ingeniería de características:

1.  **Conteo de Cambios (`med_change_count`):** Se creó una función para recorrer las 23 columnas y contar cuántas veces aparecían los términos `up` (aumento) o `down` (descenso) por paciente.
2.  **Estado del Tratamiento (`treatment_status`):** Basado en el conteo anterior, se clasificó la estabilidad del tratamiento:
    * **Stable:** 0 cambios.
    * **Low Instability:** 1 cambio.
    * **High Instability:** >1 cambio.
3.  **Simplificación:** Se eliminaron las 23 columnas de medicamentos y el contador temporal, manteniendo solo la columna de estado final.

---

## 4. 📈 Ingeniería de Atributos (Feature Engineering)

### 🔄 Reingresos (Readmission)
Se estandarizó la columna `readmitted` (valores original `<30`, `>30`, `no`) en una nueva variable llamada `readmitted_status` para facilitar la creación de gráficos descriptivos sobre reingreso temprano o tardío.

### 🔢 Edad Numérica (Age)
La columna `age` venía en rangos de texto (ej. `[10-20]`). Para permitir cálculos estadísticos (como la edad promedio):
* Se asignó el **punto medio** de cada rango (ej: `[10-20] -> 15`).
* Se almacenó en `age_numeric` y se eliminó la columna de texto original.

### 🏥 Categorización de Estancia Hospitalaria
Se transformó `time_in_hospital` en una variable categórica `hospital_stay_type` según la duración de la internación:

| Categoría | Días de Estancia |
| :--- | :--- |
| **Ambulatory** | 1 - 2 días |
| **Standard** | 3 - 4 días |
| **Moderate** | 5 - 7 días |
| **Prolonged** | 8+ días |

*Nota: Se conservó la columna numérica original para análisis de correlación en el EDA.*

---

## 5. 🔗 Enriquecimiento de Datos: `ids_mapping`

Se procesó el archivo complementario `ids_mapping` para traducir códigos numéricos en descripciones comprensibles.

1.  **Normalización del Mapeo:** El archivo original estaba desordenado. Se aplicó un bucle `for` con detección de palabras clave (`discharge`, `source`) para asignar etiquetas de categoría correctamente.
2.  **Limpieza de IDs:** Se eliminaron filas que repetían encabezados, se renombraron columnas a `id`, `description` y `category`, y se aseguraron formatos numéricos para el cruce.
3.  **Merge Estratégico:** Se realizó un **Left Join** entre el dataset principal y el mapeo procesado para enriquecer:
    * `admission_type_id`
    * `discharge_disposition_id`
    * `admission_source_id`
4.  **Post-procesamiento:** Los valores nulos resultantes del cruce se marcaron como `Unknown`.

---

## 🏁 Conclusión del Proceso

Como paso final antes de la exportación, se eliminaron residuos del proceso de unión (`category_x`, `category_y`) y columnas redundantes. 

* **Dataset Original:** 50 columnas.
* **Dataset Final:** 26 columnas optimizadas.

**Resultado:** El dataset está limpio, enriquecido y listo para realizar un análisis EDA profundo con datos estadísticamente significativos. 🚀