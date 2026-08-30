# H.52 Cline debugging order for React Flow

When the loop diagram is misaligned:

1. confirm node IDs are stable,
2. confirm the node positions,
3. confirm source/target handles,
4. confirm edge direction,
5. confirm `fitView`/viewport state,
6. confirm CSS around `.react-flow`,
7. only then adjust the dimensions.

Never “fix” edge geometry with arbitrary page transforms.

React Flow's current handle documentation confirms that explicit source/target handles and handle IDs control edge attachment points. citeturn830860search1

---

