-- Rental-investor hotspots: communities with high gross yield and deep rental demand
SELECT c.name AS community, c.n AS sales_12m, c.price_median, c.psf_median, c.psf_yoy,
       r.contracts AS rent_contracts_12m, r.rent_median, y.yield_pct,
       RANK() OVER (ORDER BY y.yield_pct DESC) AS yield_rank
FROM communities c
JOIN rents_by_community r ON r.name = c.name
JOIN yields_by_community y ON y.name = c.name
WHERE c.n >= 300 AND r.contracts >= 1000
ORDER BY y.yield_pct DESC;
