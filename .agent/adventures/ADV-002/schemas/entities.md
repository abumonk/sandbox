## Entities

### Module
- name: String (required, unique within repo)
- path: Path (absolute or repo-relative)
- language: String (python | rust | ark)
- repo_path: Path (root of the indexed repo)
- line_count: Int (>= 0)
- Relations: contains Functions, Classes; imported by other Modules

### Function
- name: String (required)
- module: String (FK -> Module.name)
- path: Path
- line: Int (start line, >= 1)
- end_line: Int (>= line)
- params: [Parameter]
- return_type: String (nullable)
- complexity: Complexity (nullable)
- decorators: [String]
- is_exported: Bool (pub in Rust, no underscore prefix in Python)
- Relations: called by Functions (CallEdge), contains Parameters, belongs to Module

### Class
- name: String (required)
- module: String (FK -> Module.name)
- path: Path
- line: Int
- end_line: Int
- bases: [String] (parent class names)
- methods: [Method]
- fields: [String]
- Relations: inherits from Classes (InheritsEdge), contains Methods, belongs to Module

### Method
- name: String (required)
- class_name: String (FK -> Class.name)
- module: String (FK -> Module.name)
- path: Path
- line: Int
- end_line: Int
- params: [Parameter]
- return_type: String (nullable)
- complexity: Complexity (nullable)
- is_static: Bool
- Relations: same as Function, plus belongs to Class

### Parameter
- name: String (required)
- type_name: String (nullable)
- default_val: String (nullable, serialized)
- position: Int (0-based)

### Variable
- name: String (required)
- scope: String (module | function | class)
- type_name: String (nullable)
- line: Int

### Edge
- source: String (FK -> node name)
- target: String (FK -> node name)
- kind: EdgeKind
- file: Path
- line: Int

### EdgeKind (enum)
- calls
- inherits_from
- imports
- contains
- overrides
- references
- ark_bridge
- ark_contains

### CallEdge (specialized Edge)
- caller: String (FK -> Function/Method name)
- callee: String (FK -> Function/Method name)
- file: Path
- line: Int
- is_dynamic: Bool

### InheritsEdge (specialized Edge)
- child: String (FK -> Class name)
- parent: String (FK -> Class name)
- file: Path
- line: Int

### ImportEdge (specialized Edge)
- importer: String (FK -> Module name)
- imported: String (FK -> Module name)
- file: Path
- line: Int
- alias: String (nullable)

### ArkEntity
- name: String (required)
- kind: String (abstraction | class | instance | island | bridge | registry | expression | predicate)
- file: Path
- inherits: [String]
- ports: { in: [String], out: [String] }
- Relations: inherits from ArkEntities, bridged to other ArkEntities

### Complexity
- function_name: String (FK -> Function.name)
- cyclomatic: Int (>= 1)
- cognitive: Int (>= 0)
- loc: Int (lines of code)
- halstead_volume: Float (>= 0)

### CodeGraph (container)
- modules: [Module]
- functions: [Function]
- classes: [Class]
- methods: [Method]
- edges: [Edge]
- metadata: GraphMetadata

### GraphMetadata
- repo_path: Path
- indexed_at: String (ISO timestamp)
- language_stats: [String: Int] (language -> file count)
- node_count: Int
- edge_count: Int
