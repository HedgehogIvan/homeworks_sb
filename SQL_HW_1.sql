SELECT head
FROM 
(
  SELECT employee, salary, MAX(date) as m_date 
  FROM salaries 
  GROUP BY employee
  ORDER BY salary DESC
  LIMIT 1
) AS max_salary
JOIN employees
ON max_salary.employee = employees.employee