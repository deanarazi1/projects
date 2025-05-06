 select *
 From layoffs;
 
 -- DATA CLEANING
 -- 1. Remove Duplicates
 -- 2. Standardize the data
 -- 3. Deal with Null values, blanks and removal of unnecessary artifacts

 -- We will not handle directly with the data since we want to keep the original DB out of mistakes and unwanted changes. We will work with a staging table instead
 Create table layoffs_staging
 like layoffs;
 
 -- Coppying everything from 'layoffs' table,
 insert layoffs_staging
 select *
 from layoffs;
 
 -- Seeing it fits and works as wanted,
 select *
 from layoffs_staging;
 
 -- 1.

-- We would like to see what are the duplicates so we add a row_num() to each row to check uniqeness
 select *,
 row_number() over(
 Partition by company, location, industry, total_laid_off,
 percentage_laid_off, `date`, country, funds_raised_millions) as row_num
 from layoffs_staging;
 
 -- Check which rows have dupliactes (those with a row_num that is bigger than 1 meaning there is more than 1 copy for that row)
 -- We will perform this with a CTE
 With duplicate_cte as
 (
 select *,
 row_number() over(
 Partition by company, location, industry, total_laid_off,
 percentage_laid_off, `date`, country, funds_raised_millions) as row_num
 from layoffs_staging
 )
 select *
 from duplicate_cte
 where row_num > 1;
 
 -- Since CTE's are not updateable we could create a staging2 table in which we could make the wanted changes
 
 CREATE TABLE `layoffs_staging2` (
  `company` text,
  `location` text,
  `industry` text,
  `total_laid_off` int DEFAULT NULL,
  `percentage_laid_off` text,
  `date` text,
  `stage` text,
  `country` text,
  `funds_raised_millions` int DEFAULT NULL,
  `row_num` INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

 -- Copy everything from layoffs_staging,
 Insert into layoffs_staging2
 select *,
 row_number() over(
 Partition by company, location, industry, total_laid_off,
 percentage_laid_off, `date`, country, funds_raised_millions) as row_num
 from layoffs_staging;
 
  -- Check the duplicates
 select *
 from layoffs_staging2
 where row_num > 1;
 
 -- Delete the duplicates
 Delete 
 from layoffs_staging2
 where row_num > 1;
 
 -- Check there are no duplicates
 select *
 from layoffs_staging2
 where row_num > 1;
 
 -- 2.
 
 -- See if there are any companies whos name has unnecessary spaces
 select company, trim(company)
 from layoffs_staging2;
 
  -- Convert companies whos name has unnecessary spaces into a standart name without them
 update layoffs_staging2
 set company = trim(company);
 
 -- Lets look at the industry column and see if it has any issues
 select distinct industry
 from layoffs_staging2
 order by industry;
 
 -- Some companies in the crypto industry are labeled as 'Crypto currency'. Redundant, lets have a look which of them are labeled differently under the same category
 select *
 from layoffs_staging2
 where industry like '%crypto%';
 
 -- convert all the 'crypto' variations into a single 'Crypto' industry name
 update layoffs_staging2
 set industry = 'Crypto'
 where industry like '%crypto%';

 -- Lets look at the country column and see if it has any issues
select distinct country
from layoffs_staging2
order by 1;

-- It seems USA has an issue with a '.' at the end. Lets have a closer look
select distinct country, trim(trailing '.' from country)
from layoffs_staging2
order by country;

-- USA has an entry at which it has a trailing '.' , lets remove it
update layoffs_staging2
set country = trim(trailing '.' from country)
where country like 'united states%';

-- The date is in text format. Lets see the difference
select `date`,
str_to_date(`date`, '%m/%d/%Y') as 'standart day format'
from layoffs_staging2;

-- Lets chagne the format into a proper date type
update layoffs_staging2
set `date` = str_to_date(`date`, '%m/%d/%Y');

-- Lets change the data-type to date
alter table layoffs_staging2
modify column `date` date;


-- 3.
-- Lets see which entries have a null or a blank 'industry' field 
select *
from layoffs_staging2
where industry is null
or industry = '';

-- A simple comparison of layoffs_staging2 with itself to look at missing 'industry' values we can complete from other entreis
select *
from layoffs_staging2 t1
join layoffs_staging2 t2
	on t1.company = t2.company
where (t1.industry is null or t1.industry = '') 
and t2.industry is not null;

-- We will set all blanks to null in order to make operations a bit simpler for us 
update layoffs_staging2
set industry = null
where industry = '' ;

-- Update the missing 'industry' Values with the values we already have with different entries
update layoffs_staging2 t1
join layoffs_staging2 t2
	on t1.company = t2.company
set t1.industry = t2.industry
where t1.industry is null
and t2.industry is not null;

-- Lets see which entries have a null 'total_laid_off' field and a null 'percentage_laid_off' field 
select *
from layoffs_staging2
where total_laid_off is null
and percentage_laid_off is null;

-- Delete them as they are practically useless
Delete
from layoffs_staging2
where total_laid_off is null
and percentage_laid_off is null;

-- Delete row_num cloumn as we have deleted all duplicate and this column provide no valuable information
alter table layoffs_staging2
drop column row_num;

-- EXPLORATORY DATA ANALYSIS

-- What was the largest lay off in a single occurence?
select max(total_laid_off)
from layoffs_staging2;

-- Who had the most people layed off as a percentage of the company? we will order by how much funds were raised in decending order
select * 
from layoffs_staging2
where percentage_laid_off = max(percentage_laid_off)
order by funds_raised_millions desc;

-- What company had the largest lay off in total?
select company, sum(total_laid_off)
from layoffs_staging2
group by company 
order by sum(total_laid_off) desc;

-- What is the time frame of the data we got?
select min(`date`), max(`date`)
from layoffs_staging2;

-- Which industry had the most laying off?
select industry, sum(total_laid_off)
from layoffs_staging2
group by industry 
order by sum(total_laid_off) desc;

-- Which country had the most laying off?
select country, sum(total_laid_off)
from layoffs_staging2
group by country 
order by sum(total_laid_off) desc;

-- What year had the most layoffs
select year(`date`), sum(total_laid_off)
from layoffs_staging2
group by year(`date`) 
order by sum(total_laid_off) desc;

-- What year whad the most layoffs
select stage, sum(total_laid_off)
from layoffs_staging2
group by stage 
order by sum(total_laid_off) desc;

-- How many layoffs happened? show by months
select substring(`date`, 1, 7) as `Month` , sum(total_laid_off)
from layoffs_staging2
where substring(`date`, 1, 7) is not null
group by `Month`
order by sum(total_laid_off) desc;

-- Show progress of layoffs with each month passing and accumulate the sum 
with Rolling_table as
(
select substring(`date`, 1, 7) as `Month` , sum(total_laid_off) as total_off
from layoffs_staging2
where substring(`date`, 1, 7) is not null
group by `Month`
order by sum(total_laid_off)
)
select `Month`,total_off, sum(total_off) over(order by `Month`) as rolling_total
from Rolling_table;

--  Identify the top 5 companies with the highest number of layoffs for each year
with company_year (company, years, total_laid_off) as 
(
select company, year(`date`) , sum(total_laid_off)
from layoffs_staging2
group by company, year(`date`)
-- That is a CTE for each years layoff in a company from layoffs_staging2
), company_year_rank as
(select *, dense_rank() over (partition by years order by total_laid_off desc) as `rank` 
from company_year
where years is not null
-- Adding a rank and ignoring null values
)
select *
from company_year_rank
where `rank` <= 5
;