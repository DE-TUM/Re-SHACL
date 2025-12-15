# Logic Comparison: Original vs Refactored

## Original Code Structure (re_shacl.py)

```
1. Load and initialize data
   - Extract target_classes, path_value, found_node_targets
   - Build same_nodes dict

2. BEFORE main loop:
   - target_domain_range(vg, found_node_targets, same_nodes, target_classes)
   - For each found_node_target:
       while not all_focus_merged:
           merge_same_focus()

3. MAIN LOOP: while (not all_targetClasses_merged OR not all_samePath_merged):
   a. merge_target_classes()
   b. target_range()
   c. merge_same_property()
   d. For each found_node_target:
       while not all_focus_merged:
           merge_same_focus()
   e. Expand found_node_targets from shape_linked_target

4. AFTER main loop:
   - For each found_node_target:
       For each (node, p, o):
           Add (node, superprop, o) for all superproperties
   - Add owl:sameAs triples from same_nodes dict
```

## Refactored Code Structure (closure_engine.py)

```
1. Load and initialize data
   - extract_merge_inputs creates discovered_focus_nodes

2. BEFORE main loop:
   - target_domain_range()
   - For all nodes with owl:sameAs relationships:
       while not all_focus_merged:
           merge_same_focus()

3. MAIN LOOP: while (not all_targetClasses_merged OR not all_samePath_merged):
   a. Phase 1:
       - merge_target_classes()
       - target_range()
   b. Phase 2:
       - merge_same_property()
   c. Step 3:
       - For all nodes with owl:sameAs relationships:
           while not all_focus_merged:
               merge_same_focus()
   d. Expand discovered_focus_nodes from shape paths + owl:sameAs neighbors

4. AFTER main loop:
   - _add_subproperty_closure: For each discovered_focus_node:
       For each (node, p, o):
           Add (node, superprop, o) for all superproperties
   - (In run_pipeline.py) Add owl:sameAs triples from same_as_dict
```

## Key Differences

### 1. Focus Node Merging Location
**Original**: Focus node merging happens TWICE - once before loop, once inside loop (step d)
**Refactored**: Focus node merging happens TWICE - once before loop, once inside loop (step 3c)
**Status**: ✓ EQUIVALENT

### 2. Focus Node Set Used for Merging
**Original**: Merges only nodes in `found_node_targets` 
**Refactored**: Merges ALL nodes with `owl:sameAs` relationships (superset of found_node_targets)
**Status**: ⚠ DIFFERENT - Refactored is MORE complete (intentional fix)

### 3. Focus Node Expansion
**Original**: 
```python
for path_ahead in shape_linked_target:
    for x in vg.objects(None, path_ahead):
        if x not in found_node_targets:
            found_node_targets.add(x)
            same_set = set()
            same_nodes.update({x: same_set})
```
**Refactored**:
```python
new = {obj for p in _shape_path_properties(g) 
       for obj in g.objects(None, p)}
# Also adds owl:sameAs neighbors
```
**Status**: ⚠ NEED TO VERIFY - Logic looks similar but needs checking

### 4. Superproperty Closure Timing
**Original**: After main loop converges
**Refactored**: After main loop converges  
**Status**: ✓ EQUIVALENT

### 5. Loop Termination Condition
**Original**: `while (not all_targetClasses_merged OR not all_samePath_merged)`
**Refactored**: `while _not_converged()` which checks same conditions
**Status**: ✓ EQUIVALENT

## Potential Issues to Investigate

1. **_shape_path_properties() implementation**:
   - Does it correctly match `shape_linked_target`?
   - Original builds `shape_linked_target` from property shapes with SH_node
   
2. **Target extraction differences**:
   - Check if `extract_merge_inputs` captures all the same targets as original
   - Verify `global_path` handling
   
3. **Convergence check**:
   - Original uses `found_node_targets` set
   - Refactored uses `discovered_focus_nodes` set
   - Are these being populated identically?

4. **same_as_dict initialization**:
   - Original: `for f in found_node_targets: same_set = set(); same_nodes.update({f: same_set})`
   - Refactored: In extract_merge_inputs
   - Timing of when new nodes get added to dict matters

## Next Steps

1. Compare `shape_linked_target` (original) vs `_shape_path_properties()` (refactored)
2. Verify node expansion logic adds same nodes at same time
3. Check if any nodes are missing from discovered_focus_nodes that should be there
