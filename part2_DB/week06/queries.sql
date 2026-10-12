-- queries.sql
-- OTB Fossil Database Queries
-- Week 6 Assignment

-- ── Query 1 ───────────────────────────────────────────────────────────────────
-- Question: How many fossil specimens are in the database?
-- Write a SELECT query that returns the total row count of the fossils table.
-- Counts every row in fossils and gives the total size of the OTBM sample.
SELECT COUNT(*) FROM fossils;


-- ── Query 2 ───────────────────────────────────────────────────────────────────
-- Question: Which specimens were discovered by Kamoya Kimeu?
-- Write a SELECT query returning catalog_number, preparations, and year
-- for all fossils where discovered_by contains 'Kimeu',
-- ordered by year ascending.
-- Searches and matches all iterations of Kimeu like K. Kimeu or Kamoya Kimeu
SELECT catalog_number, preparations, year
FROM fossils
WHERE discovered_by LIKE '%Kimeu%'
ORDER BY year ASC;

-- ── Query 3 ───────────────────────────────────────────────────────────────────
-- Question: How many specimens come from each formation?
-- Write a SELECT query that joins fossils to localities, groups by formation,
-- and returns the formation name and specimen count, ordered by count descending.
-- Joins fossils to localities to get each specimens formation then counts the specimens PER formation. 
SELECT l.formation, COUNT(*) AS n
FROM fossils f
JOIN localities l ON f.locality_id = l.locality_id
GROUP BY l.formation
ORDER BY n DESC;

-- ── Query 4 ───────────────────────────────────────────────────────────────────
-- Question: Which specimens are older than 3 million years?
-- Write a SELECT query returning catalog_number, scientific_name,
-- earliest_chronometric_age, and formation for fossils where
-- earliest_chronometric_age > 3.0, ordered by age descending.
-- This requires joining fossils to both taxa and localities.
-- Joins fossils to both taxa and localities and filters >3MYA by oldest first. Shows which taxa and formations make up the Pliocene record.
SELECT f.catalog_number, t.scientific_name, f.earliest_chronometric_age, l.formation
FROM fossils f
JOIN taxa t ON f.taxon_id = t.taxon_id
JOIN localities l ON f.locality_id = l.locality_id
WHERE f.earliest_chronometric_age > 3.0
ORDER BY f.earliest_chronometric_age DESC;

-- ── Query 5 ───────────────────────────────────────────────────────────────────
-- Question: Which taxon has the most specimens, and what anatomical
-- elements are most commonly preserved for that taxon?
-- Write two queries:
-- (a) Find the scientific_name with the highest specimen count.
-- Counts specimens per scientific name and keeps only the top one
SELECT t.scientific_name, COUNT(*) AS n
FROM fossils f
JOIN taxa t ON f.taxon_id = t.taxon_id
GROUP BY t.scientific_name
ORDER BY n DESC
LIMIT 1;
-- (b) For that taxon, show the distribution of preparations values
--     with counts, ordered by count descending.
-- Replaces the name below with the eaxct result from 5a.
SELECT f.preparations, COUNT(*) AS n
FROM fossils f
JOIN taxa t ON f.taxon_id = t.taxon_id
WHERE t.scientific_name = 'Hominini'
GROUP BY f.preparations
ORDER BY n DESC;
