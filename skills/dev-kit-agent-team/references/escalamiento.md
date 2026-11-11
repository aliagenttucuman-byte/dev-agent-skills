# Escalamiento entre agentes

> Cuando un agente no puede seguir, el escalamiento es un procedimiento con
> formato, no una queja en el chat.

## Principio

> **Escalar antes es barato. Escalar despues es caro.** Un agente que se
> traba y sigueWorking produce codigo que hay que descartar.

## Cuando escalar

### Escalamiento de alcance (el contrato no alcanza)

El agente descubre que el contrato no cubre lo que necesita.

1. **Detener** el trabajo en esa parte. No implementar "a ojo".
2. **Documentar** el caso concreto: entrada, comportamiento esperado,
   comportamiento actual del contrato.
3. **Escalar** al arquitecto con ese caso.
4. **Esperar** contrato actualizado. No seguir con la version anterior.

### Escalamiento de capas (el fallo cruza capas)

El mismo fallo aparece en dos capas a la vez.

1. **Aislar** el fallo en la capa donde aparece primero.
2. **Verificar** en esa capa con el artefacto anterior que funcionaba.
3. **Partir** el fallo en una parte por capa.
4. **Asignar** cada parte a su dueno.

Si las dos capas fallan por la misma causa, la causa esta en una capa mas
abajo: se sigue bajando hasta encontrar el dueno.

### Escalamiento de estrategia (el agente se repite)

El agente falla con el mismo error dos veces.

- **No** se reintenta identico. Un reintento identico no es un reintento: es
  tiempo quemado con la misma variable.
- Se cambia la estrategia: cambiar el enfoque, pedir un contrato mas
  detallado, o reasignar a otro agente del mismo rol.
- Si el segundo enfoque tambien falla, el problema no es el agente: es la
  descomposicion. Vuelve al orquestador.

### Escalamiento de alcance de producto

El trabajo resulta mayor que lo que el plan permitia.

- Se detiene la implementacion.
- Se vuelve a la fase de estimacion (ver `dev-kit-sdd-workflow`).
- Se actualiza la estimacion antes de seguir. Ampliar sin estimar es la forma
  mas comun de perder presupuesto sin notarlo.

## Ruta de escalamiento

```
agente de trabajo
      |
      | el contrato no alcanza
      v
arquitecto
      |
      | la eleccion de diseno no cierra
      v
lider tecnico
      |
      | el alcance del producto cambia
      v
decision de producto
```

El orquestador mantiene la ruta, pero no es un escalon por si mismo: escala
**a alguien con autoridad sobre esa dimension**.

## Formato del aviso de escalamiento

```
ESCALAMIENTO
- Desde:      <rol de origen>
- A:          <rol de destino>
- Tarea:      <id>
- Tipo:       contrato | capas | estrategia | alcance
- Sintoma:    <que se observa, en una frase>
- Esperado:   <que deberia pasar>
- Evidencia:  <salida exacta, test que falla, log>
- Impacto:    <que queda bloqueado>
- Propuesta:  <opcion A> | <opcion B>
- Sugerencia: <lo que el orquestador hará si nadie responde>
```

La ultima linea importa: define que pasa si el escalamiento no se responde.
Sin ella, el escalamiento se pierde en el silencio.

## Anti-patrones de escalamiento

| Anti-patron | Por que falla |
|---|---|
| Escalar sin evidencia | Nadie puede decidir sin ver el fallo |
| Escalar y seguir trabajando en paralelo | Se produce codigo sobre una base que puede cambiar |
| Escalar tres veces lo mismo | La primera escalamiento no se leyo o no se entendio |
| "No puedo" sin opciones | El escalamiento sin propuesta devuelve el problema al mismo lugar |
| Dejar el escalamiento sin respuesta posible | El trabajo queda congelado sin dueño |
