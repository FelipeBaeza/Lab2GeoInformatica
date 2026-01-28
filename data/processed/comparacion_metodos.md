# Comparación de Métodos de Detección de Cambios
## Laboratorio 2: Detección de Cambios Urbanos - Chaitén

---

## Método 1: Diferencia de Índices (NDVI)

### Descripción
Calcula la diferencia simple de NDVI entre dos fechas y clasifica los píxeles según umbrales.

### Fórmula
```
Diferencia = NDVI_t2 - NDVI_t1

Si Diferencia < -umbral → Pérdida de vegetación
Si Diferencia > +umbral → Ganancia de vegetación
Si |Diferencia| ≤ umbral → Sin cambio significativo
```

### Resultados
- Píxeles con pérdida: 10,785 (26.96%)
- Píxeles con ganancia: 836 (2.09%)
- Diferencia media NDVI: -0.0802 ± 0.1135

### Ventajas
- ✅ Simple y rápido de implementar
- ✅ Fácil de interpretar
- ✅ Pocos parámetros a calibrar
- ✅ Robusto para detectar cambios de vegetación

### Desventajas
- ❌ Solo detecta cambios en vegetación
- ❌ No distingue tipos de cambio (urbanización vs otros)
- ❌ Sensible a variaciones estacionales
- ❌ No utiliza información de otros índices

---

## Método 2: Clasificación Multiíndice de Cambio Urbano

### Descripción
Combina NDVI, NDBI y NDWI para clasificar diferentes tipos de cambio usando reglas basadas en umbrales múltiples.

### Reglas de Clasificación
```
1. Urbanización: 
   Era vegetación (NDVI_t1 > 0.3) Y Es urbano (NDBI_t2 > 0) Y Cayó NDVI
   
2. Pérdida de vegetación: 
   NDVI_t1 - NDVI_t2 > umbral (no clasificado como urbanización)
   
3. Ganancia de vegetación: 
   NDVI_t2 - NDVI_t1 > umbral
   
4. Nuevo cuerpo de agua: 
   No era agua (NDWI_t1 < 0) Y Es agua (NDWI_t2 > 0.1)
   
5. Pérdida de agua: 
   Era agua (NDWI_t1 > 0.1) Y No es agua (NDWI_t2 < 0)
```

### Resultados
- Urbanización: 1,734 (4.33%)
- Pérdida Vegetación: 9,051 (22.63%)
- Ganancia Vegetación: 836 (2.09%)
- Nuevo Cuerpo Agua: 0 (0.00%)
- Pérdida Agua: 0 (0.00%)


### Ventajas
- ✅ Distingue múltiples tipos de cambio
- ✅ Identifica específicamente urbanización
- ✅ Utiliza información espectral complementaria
- ✅ Mejor caracterización del tipo de transición

### Desventajas
- ❌ Más complejo de implementar
- ❌ Requiere calibración de múltiples umbrales
- ❌ Orden de reglas afecta clasificación
- ❌ Puede haber confusión entre clases

---

## Comparación Cuantitativa

| Aspecto | Método 1 (Diferencia) | Método 2 (Multiíndice) |
|---------|----------------------|------------------------|
| Complejidad | Baja | Media |
| Parámetros | 1 (umbral) | 4 (umbrales) |
| Clases detectadas | 3 | 6 |
| Tipo de cambio | Solo vegetación | Múltiples |
| Velocidad | Muy rápida | Rápida |
| Interpretabilidad | Alta | Media |

---

## Justificación de Umbrales

### Umbral de cambio mínimo (0.15)
- Cambios de NDVI menores a 0.15 pueden deberse a:
  - Variaciones atmosféricas entre fechas
  - Diferencias fenológicas estacionales menores
  - Ruido del sensor
- El valor 0.15 (~15% de cambio) es un umbral conservador que reduce falsos positivos

### Umbral de vegetación NDVI (0.3)
- Valores típicos de NDVI:
  - Agua/Superficies construidas: -0.1 a 0.1
  - Suelo desnudo: 0.1 a 0.2
  - Vegetación dispersa: 0.2 a 0.4
  - Vegetación densa: 0.4 a 0.9
- El umbral 0.3 separa vegetación activa de suelo/urbano

### Umbral de área urbana NDBI (0.0)
- NDBI positivo indica mayor reflectancia SWIR que NIR
- Típico de superficies impermeables (techos, asfalto, hormigón)
- Valores negativos indican vegetación o agua

### Umbral de agua NDWI (0.1)
- NDWI > 0.1 indica alta probabilidad de presencia de agua
- Valores más conservadores reducen confusión con sombras

---

## Recomendaciones

1. **Para análisis rápido**: Usar Método 1 (Diferencia de Índices)
2. **Para caracterización detallada**: Usar Método 2 (Clasificación Multiíndice)
3. **Para validación**: Comparar resultados de ambos métodos
4. **Para zonas urbanas específicas**: El Método 2 es preferible

---

## Archivos Generados

- `cambio_diferencia_ndvi.tif`: Resultado Método 1 (-1, 0, +1)
- `cambio_clasificado.tif`: Resultado Método 2 (0-5 clases)
- `comparacion_metodos.md`: Este archivo

---

*Generado automáticamente por detect_changes.py*
