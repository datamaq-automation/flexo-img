# Lean Canvas — preflight antes de fabricar la plancha

Ignacio / TrainPulga, con asistencia de Codex. Entrega de diciembre para [#1](https://github.com/datamaq-automation/flexo-img/issues/1) y [#2](https://github.com/datamaq-automation/flexo-img/issues/2). Diseño de producto para validar, no negocio ya operativo.

## 1. Problema
Un original con resolución insuficiente, separación incorrecta o líneas demasiado finas puede provocar retrabajo, demoras y desperdicio al fabricar una plancha. La consigna plantea ese riesgo; no medimos su frecuencia ni su costo en el taller del profesor. Inspeccionar antes permite pedir correcciones sin fabricar primero.

## 2. Segmentos de clientes
Usuario previsto: operador de preprensa. El responsable técnico define aceptación y el diseñador corrige el original. Posibles compradores: dueño o responsable de producción de talleres de flexografía, etiquetas o packaging; agencias podrían usarlo antes de enviar archivos. Son hipótesis, no clientes entrevistados ni ventas confirmadas.

## 3. Propuesta de valor única
Hacer visible qué contiene un archivo y cómo queda separado antes de decidir fabricar, con evidencia reproducible y datos desconocidos explícitos. Diciembre demuestra inspección y separación; no promete certificar automáticamente la plancha ni ahorrar un importe determinado.

## 4. Solución
CLI local multiformato, informe de entrada, rasterización explícita, conversión/separación CMYK, cuatro canales y comparación visual. Tramado y aptitud se integrarán y validarán en febrero; los experimentos previos quedan respaldados fuera de esta entrega. La decisión de fabricar sigue siendo del responsable del taller.

## 5. Canales
Repositorio, README y demostración local al profesor/operador; acompañamiento y capacitación como posible vía de adopción. Una integración con recepción de pedidos sería futura: no hay sitio web ni servicio desplegado en este alcance.

## 6. Ingresos e inserción laboral
**A. Relación de dependencia:** desarrollar capacidades para automatización de preprensa e integración técnica en una empresa gráfica o de packaging. No se afirma que ya exista empleo o remuneración.

**B. Servicio independiente:** ofrecer instalación, configuración y soporte, quizás mediante abono o trabajo puntual para talleres. Hay que validar necesidad, compatibilidad con RIP, licencias y disposición a pagar. Precios, presupuesto, márgenes y ventas son pendientes, no datos confirmados. El aprendizaje puede convertirse en servicio; no se afirma que ya genere ingresos.

## 7. Estructura de costos
Tiempo de desarrollo, capacitación y soporte; cómputo y almacenamiento; gestión de ICC; muestras y pruebas físicas. Revisar licencias abiertas antes de distribuir o comercializar: abierto no significa sin obligaciones. No hay importes ni costos del taller medidos.

## 8. Métricas clave
Proponer un piloto con originales autorizados y un dictamen humano de referencia: tiempo de revisión antes/después, falsos rechazos, errores no detectados, correcciones pedidas y retrabajos de plancha confirmados. Medir recursos y latencia por tamaño/máquina. Calcular ahorro solo con costos observados comparables y descontando operación/soporte; no inferirlo del número de tests ni de esta demo.

## 9. Ventaja diferencial
Hipótesis: reglas configurables para el taller, resultados transparentes y adaptación local facilitan auditoría y aprendizaje. No se afirma superioridad probada frente a licencias comerciales, equivalencia con un RIP ni aptitud industrial actual.

## Qué confirmar
Quién recibe/aprueba y quién pagaría; formatos/volúmenes habituales; fallas y costo de retrabajo; tiempos de revisión; máquina, plancha, sustrato, tintas, RIP, ICC, LPI y polaridad. Pedir muestra de packaging autorizada y prueba física. La demostración de diciembre no requiere fabricar una plancha.
