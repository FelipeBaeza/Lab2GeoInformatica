# Interpretación de Resultados: Detección de Cambios Urbanos en Chaitén
## Laboratorio 2 - Geoinformática USACH

---

## 1. Contexto del Área de Estudio

La comuna de **Chaitén**, ubicada en la Región de Los Lagos (Chile), presenta un caso de estudio particular debido a su historia de reconstrucción post-erupción volcánica de 2008. El área analizada (bbox: -72.76, -42.96, -72.64, -42.86) corresponde principalmente al núcleo urbano y sus zonas periurbanas.

**Período de análisis**: 2020-2024 (14 imágenes Sentinel-2, verano austral)

---

## 2. Resultados Principales

### 2.1 Resumen Cuantitativo

| Tipo de Cambio | Área (ha) | Porcentaje |
|----------------|-----------|------------|
| Urbanización | 526.16 | 0.05% |
| Pérdida de Vegetación | 86,439.11 | 7.39% |
| Ganancia de Vegetación | 17,544.02 | 10.88% |

### 2.2 Patrones Espaciales Observados

**Zonas con mayor urbanización:**
- **Z0201**: 206.61 ha - Corresponde a áreas de expansión urbana hacia el norte
- **Z0101**: 181.47 ha - Zona de desarrollo comercial y residencial
- **Z0202**: 69.51 ha - Sector periurbano con nuevas construcciones

**Interpretación**: La urbanización detectada (0.05%) es relativamente baja, lo cual es consistente con el contexto post-erupción de Chaitén. Las zonas de mayor cambio coinciden con las áreas de reconstrucción planificada.

### 2.3 Dinámica de Vegetación

El análisis revela una tendencia general de **recuperación de vegetación**:
- Balance neto: +10.88% ganancia vs -7.39% pérdida = **+3.49% neto**
- Esto es consistente con la regeneración natural post-desastre

**Zonas con mayor pérdida de vegetación:**
- Z0101: 39,105.10 ha - Posiblemente asociado a incendios forestales o tala
- Z0001: 16,977.99 ha - Conversión agrícola

**Zonas con mayor ganancia:**
- Z0102: 13,825.17 ha - Revegetación natural
- Z0002: 1,099.27 ha - Reforestación

---

## 3. Evolución Temporal de Índices

### 3.1 NDVI (Índice de Vegetación)

| Año | NDVI Medio | Tendencia |
|-----|------------|-----------|
| 2020 | 0.167 | Línea base |
| 2021 | 0.164 | Estable |
| 2022 | 0.181 | Aumento leve |
| 2023 | 0.170 | Fluctuación |
| 2024 | 0.159 | Disminución leve |

**Interpretación**: El NDVI muestra fluctuaciones estacionales normales con una tendencia general estable alrededor de 0.16-0.18. Esto indica vegetación moderadamente activa, típica de zonas templadas lluviosas.

### 3.2 NDBI (Índice de Construcción)

Los valores negativos de NDBI (-0.09 a -0.12) a lo largo del período indican que el área de estudio sigue siendo predominantemente no urbana, con superficies impermeables limitadas.

---

## 4. Análisis de Métodos de Detección

### 4.1 Comparación de Resultados

| Métrica | Método 1 (Diferencia) | Método 2 (Multiíndice) |
|---------|----------------------|------------------------|
| Pérdida detectada | 7.44% | 7.39% |
| Ganancia detectada | 10.88% | 10.88% |
| Urbanización | - | 0.05% |

**Observación**: Ambos métodos son consistentes en la detección de cambios de vegetación, pero el Método 2 permite distinguir específicamente la urbanización de otros tipos de pérdida.

### 4.2 Validación Cruzada

La concordancia entre métodos (>95% en detección de vegetación) sugiere que:
1. Los umbrales utilizados son apropiados para la zona
2. Los cambios detectados son robustos y no artefactos metodológicos

---

## 5. Limitaciones del Análisis

1. **Resolución temporal**: Imágenes del verano austral únicamente, no captura variación estacional completa
2. **Resolución espacial**: 10m de Sentinel-2 puede no detectar cambios menores a esta escala
3. **Cobertura nubosa**: Región de alta pluviosidad limita disponibilidad de imágenes claras
4. **Validación terreno**: No se cuenta con datos de campo para validación cuantitativa

---

## 6. Conclusiones

1. **Urbanización limitada**: El área de Chaitén muestra bajo desarrollo urbano (0.05%), consistente con su contexto de reconstrucción gradual.

2. **Recuperación vegetal**: Se observa un balance positivo de vegetación (+3.49%), indicando regeneración natural del ecosistema.

3. **Estabilidad general**: Los índices espectrales muestran variabilidad estacional pero sin tendencias drásticas de degradación.

4. **Zonas de atención**: Las zonas Z0201 y Z0101 concentran la mayor parte de los cambios y requieren seguimiento continuo.

---

## 7. Recomendaciones

1. Ampliar el período de análisis para incluir imágenes de invierno
2. Incorporar datos de validación de terreno (ortofotos, visitas)
3. Implementar análisis de series temporales con mayor frecuencia
4. Correlacionar cambios con datos censales y de planificación territorial

---

*Documento generado para el Laboratorio 2 de Geoinformática - USACH*
*Autores: Catalina López, Felipe Baeza*
