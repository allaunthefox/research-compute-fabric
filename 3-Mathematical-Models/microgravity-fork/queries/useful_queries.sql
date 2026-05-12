-- Microgravity Fork — Useful Queries
-- Database: physics_microgravity.db

-- 1. See what vanishes/transforms/becomes dominant
SELECT gravity_status, COUNT(*) as equations
FROM equations
GROUP BY gravity_status
ORDER BY CASE gravity_status
    WHEN 'vanishes' THEN 1
    WHEN 'transforms' THEN 2
    WHEN 'becomes_dominant' THEN 3
    ELSE 4
END;

-- 2. List equations that vanish
SELECT e.eq_number, e.title, d.name as domain, d.ontological_layer
FROM equations e
JOIN domains d ON e.domain_id = d.id
WHERE e.gravity_status = 'vanishes'
ORDER BY d.ontological_layer, e.eq_number;

-- 3. List equations that become dominant
SELECT e.eq_number, e.title, d.name as domain, d.ontological_layer
FROM equations e
JOIN domains d ON e.domain_id = d.id
WHERE e.gravity_status = 'becomes_dominant'
ORDER BY d.ontological_layer, e.eq_number;

-- 4. ISS experiments with verified predictions
SELECT experiment_name, agency, physics_regime,
       SUBSTR(key_finding, 1, 100) as finding,
       prediction_verified
FROM iss_experiments
ORDER BY id;

-- 5. Proposals by priority
SELECT acronym, title, principal_regime, trl_level, priority, estimated_crew_hours
FROM iss_experiment_proposals
ORDER BY CASE priority WHEN 'Highest' THEN 1 WHEN 'High' THEN 2 ELSE 3 END;

-- 6. Chiral state of genetic constraint subgraph
SELECT e.eq_number, ce.chiral_state, ce.chiral_residual, ce.chiral_agreement,
       e.title
FROM chiral_encoding ce
JOIN equations e ON ce.equation_id = e.id
ORDER BY ce.chiral_residual DESC;

-- 7. Domain coverage in the fork
SELECT d.name,
       COUNT(DISTINCT e.id) as equations,
       COUNT(DISTINCT v.id) as verifications,
       ROUND(AVG(COALESCE(vc.c,0)), 1) as avg_refs
FROM domains d
JOIN equations e ON e.domain_id = d.id
LEFT JOIN verifications v ON v.equation_id = e.id
LEFT JOIN (SELECT equation_id, COUNT(*) c FROM verifications GROUP BY equation_id) vc
    ON vc.equation_id = e.id
GROUP BY d.id
ORDER BY avg_refs DESC;

-- 8. The Kelly chiral crossing — equations involved
SELECT e.eq_number, e.title, ce.chiral_state, ce.chiral_residual
FROM chiral_encoding ce
JOIN equations e ON ce.equation_id = e.id
WHERE ce.equation_id IN (593, 594, 744, 741, 605, 324)
ORDER BY ce.chiral_residual DESC;

-- 9. Biophysics/DNA regime split
SELECT constraint_regime, chiral_state, COUNT(*) as count
FROM genetic_possibility_graph
GROUP BY constraint_regime, chiral_state
ORDER BY constraint_regime, chiral_state;

-- 10. Full fork metadata
SELECT key, value FROM fork_metadata;
