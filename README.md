## :warning: Please read these instructions carefully and entirely first
* Clone this repository to your local machine.
* Use your IDE of choice to complete the assignment.
* When you have completed the assignment, you need to  push your code to this repository and [mark the assignment as completed by clicking here](https://app.snapcode.review/submission_links/311df60b-51c3-491e-8cad-35d8e7766802).
* Once you mark it as completed, your access to this repository will be revoked. Please make sure that you have completed the assignment and pushed all code from your local machine to this repository before you click the link.

**Table of Contents**
1. [Before you start](#before-you-start), a brief explanation for the exercise and software prerequisites/setup.  
2. [Tips for what we are looking for](#tips-on-what-were-looking-for) provides clear guidance on solution qualities we value 
3. [The Challenge](#begin-the-two-part-challenge) explains the data engineering code challenge to be tackled.
4. [Follow-up Questions](#follow-up-questions) related to the challenge which you should address  
5. [Your approach and answers to follow-up questions](#your-approach-and-answers-to-follow-up-questions-) is where you should include the answers to the follow-up question and clarify your solution approach any assumptions you have made.

## Before you start
### Why complete this task?

We want to make the interview process as simple and stress-free as possible. That’s why we ask you to complete 
the first stage of the process from the comfort of your own home.

Your submission will help us to learn about your skills and approach. If we think you’re a good fit for our 
network, we’ll use your submission in the next interview stages too.

### About the task

You’ll be creating an ingestion process to ingest files containing vote data. You’ll also create a means to 
query the ingested data to determine outlier weeks.

There’s no time limit for this task, but we expect it to take less than 2 hours.

### Setup Instructions

For instructions on how to set up and run the exercise, please see [SETUP.md](SETUP.md).

### Tips on what we’re looking for


* ✅  **Test coverage**

    Your solution must have good test coverage, including common execution paths.

* ✅  **Self-contained tests**

    Your tests should be self-contained, with no dependency on being run in a specific order.

* ✅  **Simplicity**

    We value simplicity as an architectural virtue and a development practice. Solutions should reflect the difficulty of the assigned task, and shouldn’t be overly complex. We prefer simple, well tested solutions over clever solutions. 

    Please avoid:

   * ❌ unnecessary layers of abstraction
   * ❌ patterns
   * ❌ custom test frameworks
   * ❌ architectural features that aren’t called for
   * ❌ libraries like **pandas** or **polars** or frameworks like **PySpark** or **ballista**
  
     We know that this exercise can be
     solved fairly trivially using these libraries and a Dataframe approach, and we'd encourage appropriate 
     use of these in daily work contexts. But for this small exercise we really 
     want to know more about how you structure, write and test your Python code,
     and want you to show some fluency in SQL -- a **pandas**
     solution won't allow us to see much of that.

* ✅  **Self-explanatory code**

    The solution you produce must speak for itself. Multiple paragraphs explaining the solution is a sign 
    that the code isn’t straightforward enough to understand on its own.
    However, please do explain your non-obvious _choices_ e.g. perhaps why you decided to load
    data a specific way.

* ✅ **Demonstrate fluency with data engineering concepts**
   
   Even though this is a toy exercise, treat DuckDB as you would an OLAP 
   data warehouse. Choose datatypes, data loading methods, optimisations and data models that 
   are suited for resilient analytics processing at scale, not transaction processing.

* ✅ **Dealing with ambiguity**

    If there’s any ambiguity, please add this in a section at the bottom of the README. 
    You should also make a choice to resolve the ambiguity and proceed.

Our review process starts with a very simplistic test set in the `tests/exercise_tests` folder which you should also
check before submission. You can run these with:
```shell
poetry run exercise check-ingestion
poetry run exercise check-outliers
```

Expect these to fail until you have completed the exercise.

You should not change the `tests/exercise-tests` folder and your solution should be able to pass both tests.


## Download the dataset for the exercise
Run the command
```
poetry run exercise fetch-data
```

which will fetch the dataset, uncompress it and place it in `uncommitted/votes.jsonl` for you.
Explore the data to see what values and fields it contains (no need to show how you explored it).

## Begin the two-part challenge
There are two parts to the exercise, and you are expected to complete both. 
A user should be able to execute each task independently of the other. 
For example, ingestion shouldn't cause the outliers query to be executed.

### Part 1: Ingestion
Create a schema called `blog_analysis`.
Create an ingestion process that can be run on demand to ingest files containing vote data. 
You should ensure that data scientists, who will be consumers of the data, do not need to consider 
duplicate records in their queries. The data should be stored in a table called `votes` in the `blog_analysis` schema. 

### Part 2: Outliers calculation
Create a view named `outlier_weeks`  in the `blog_analysis` schema. It will contain the output of a SQL calculation for which weeks are regarded as outliers based on the vote data that was ingested.
The view should contain the year, week number and the number of votes for the week _for only those weeks which are determined to be outliers_, according to the following rule:

NB! If you're viewing this Markdown document in a viewer
where the math isn't rendering, try viewing this README in GitHub on your web browser, or [see this pdf](docs/calculating_outliers.pdf).

> 
> **A week is classified as an outlier when the total votes for the week deviate from the average votes per week for the complete dataset by more than 20%.**</br>  
> For the avoidance of doubt, _please use the following formula_: 
>  
> > Say the mean votes is given by $\bar{x}$ and this specific week's votes is given by $x_i$. 
> > We want to know when $x_i$ differs from $\bar{x}$ by more than $20$%. 
> > When this is true, then the ratio $\frac{x_i}{\bar{x}}$ must be further from $1$ by more than $0.2$, i.e.: </br></br> 
> > $\big|1 - \frac{x_i}{\bar{x}}\big| > 0.2$

The data should be sorted in the view by year and week number, with the earliest week first.

Running `outliers.py` should recreate the view and 
just print the contents of this `outlier_weeks` view to the terminal - don't do any more calculations after creating the view.

## Example

The sample dataset below is included in the test-resources folder and can be used when creating your tests.

Assuming a file is ingested containing the following entries:

```
{"Id":"1","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-02T00:00:00.000"}
{"Id":"2","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-09T00:00:00.000"}
{"Id":"4","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-09T00:00:00.000"}
{"Id":"5","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-09T00:00:00.000"}
{"Id":"6","PostId":"5","VoteTypeId":"3","CreationDate":"2022-01-16T00:00:00.000"}
{"Id":"7","PostId":"3","VoteTypeId":"2","CreationDate":"2022-01-16T00:00:00.000"}
{"Id":"8","PostId":"4","VoteTypeId":"2","CreationDate":"2022-01-16T00:00:00.000"}
{"Id":"9","PostId":"2","VoteTypeId":"2","CreationDate":"2022-01-23T00:00:00.000"}
{"Id":"10","PostId":"2","VoteTypeId":"2","CreationDate":"2022-01-23T00:00:00.000"}
{"Id":"11","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-30T00:00:00.000"}
{"Id":"12","PostId":"5","VoteTypeId":"2","CreationDate":"2022-01-30T00:00:00.000"}
{"Id":"13","PostId":"8","VoteTypeId":"2","CreationDate":"2022-02-06T00:00:00.000"}
{"Id":"14","PostId":"13","VoteTypeId":"3","CreationDate":"2022-02-13T00:00:00.000"}
{"Id":"15","PostId":"13","VoteTypeId":"3","CreationDate":"2022-02-20T00:00:00.000"}
{"Id":"16","PostId":"11","VoteTypeId":"2","CreationDate":"2022-02-20T00:00:00.000"}
{"Id":"17","PostId":"3","VoteTypeId":"3","CreationDate":"2022-02-27T00:00:00.000"}
```

Then the following should be the content of your `outlier_weeks` view:


| Year | WeekNumber | VoteCount |
|------|------------|-----------|
| 2022 | 0          | 1         |
| 2022 | 1          | 3         |
| 2022 | 2          | 3         |
| 2022 | 5          | 1         |
| 2022 | 6          | 1         |
| 2022 | 8          | 1         |

**Note that we strongly encourage you to use this data as a test case to ensure that you have the correct calculation!**

## Follow-up Questions

Please include instructions about your strategy and important decisions you made in the README file. You should also include answers to the following questions, please make sure these are answered without the use AI tools as we would like to understand your thought process:

1. What kind of data quality measures would you apply to your solution in production?
2. What would need to change for the solution scale to work with a 10TB dataset with 5GB new data arriving each day?
3. Please tell us in your modified README about any assumptions you have made in your solution (below).


## Your Approach and answers to follow-up questions 

_Please provide an explaination to your implementation approach and the additional questions **here**_

## AI Tool Usage

While we encourage the use of AI tools as part of the learning process but to ensure transparency, please provide the following information regarding the use of AI tools in this submission:

1.  **Specific Use Cases:** Describe for what purposes tool was used (e.g., code generation, debugging assistance, query generation etc.).
2.  **Percentage of Code Generated by AI:** Provide an estimate of the percentage of the submitted code that was generated by AI.
3.  **How AI-Generated Code Was Reviewed:** Explain how you reviewed and verified the AI-generated code to ensure its correctness and quality.

Please note, during the technical interview, which will build upon this exercise, we'll focus on your coding abilities and problem-solving skills without the use of AI tools. This will allow us to see your direct approach and thought process.

## My Approach and answers to follow-up questions

**Implementation Approach**

**Part 1: Ingestion (ingest.py)**

The ingestion script does three things:

First, it creates the blog_analysis schema and votes table if they don't already exist. This means you can safely run it multiple times without it crashing.
Second, it uses DuckDB's read_json_auto() to load the entire JSONL file in a single SQL statement. This is the right approach for a warehouse — bulk loading is always preferred over inserting row by row.
Third, it uses INSERT OR IGNORE with a PRIMARY KEY on Id. This is how duplicates are handled — if a record with the same Id already exists, it gets skipped silently. So running ingestion twice on the same file always gives you the same result.
I chose INSERT OR IGNORE over approaches like delete-and-reinsert because it's simpler and safe enough for this use case. The Id field is the natural unique identifier, so using it as the primary key felt like the obvious choice.
One more thing — all JSON fields come in as strings, so I explicitly cast them to proper types (INTEGER, TIMESTAMP) at load time. This avoids any silent type issues when analysts query the data later.

**Part 2: Outliers (outliers.py)**

The outlier view is built using two CTEs:

weekly_votes counts how many votes happened in each week of each year
mean_votes calculates the average votes per week across the whole dataset

Then the filter applies the formula from the README:
|1 - (week_votes / mean_votes)| > 0.2
One decision worth explaining is the week numbering. I used strftime('%W') which gives Sunday-based week numbers starting from 0. I tried this against the sample data in the README and it matched the expected output exactly (weeks 0 through 8). ISO week numbering starts on Monday and gave different results, so I went with %W.
The view is recreated every time outliers.py runs using CREATE OR REPLACE VIEW. After that it just prints the contents — nothing else.

## 1. What kind of data quality measures would you apply to your solution in production?
A few things I'd put in place:

Validate before loading — check that all required fields (Id, PostId, VoteTypeId, CreationDate) are present and in the right format before trying to insert anything. Bad records should fail loudly, not silently.
Check field values make sense — for example, flag any VoteTypeId values that aren't in the known valid set, or any CreationDate that's way off in the past or future.
Track duplicates — log how many rows were skipped on each ingestion run. If suddenly a lot of records are being skipped, that's a sign something is wrong upstream.
Row count checks — after each load, compare how many lines were in the source file vs how many rows were actually inserted. A big gap deserves an alert.
Freshness monitoring — keep track of the most recent CreationDate that was loaded. If no new data has arrived in a while, something may have broken in the pipeline.


## 2. What would need to change for the solution to scale to work with a 10TB dataset with 5GB new data arriving each day?
The current solution works well for this scale but would need some changes for 10 TB:

Switch file format — JSONL is fine for small data but at this scale I'd move to Parquet. It's columnar and compressed, so it's much faster to scan and significantly smaller on disk.
Incremental loads — instead of reloading everything each time, only process new files each day. A simple tracking table (filename + row count + load timestamp) ensures each file is only processed once.
Partition the table — partitioning votes by year or month means queries only scan the data they actually need rather than the full table.
Scale out the warehouse — DuckDB is great for single-machine analytics but 10 TB is pushing it. At that point I'd look at something like Snowflake or BigQuery, or at least use DuckDB to read Parquet files directly from cloud storage (S3/GCS).
Materialise the outlier result — at scale, having a live view recompute on every query gets expensive. Better to materialise it as a table on a schedule.


## 3. Assumptions
A few things I assumed while building this:

Id is the right deduplication key. It's the only unique identifier in the data, so it made sense to use it as the primary key and deduplicate on it.
Week numbers should be Sunday-based. I used strftime('%W') which numbers weeks starting from Sunday (week 0). This was the only approach that matched the expected output in the README sample exactly.
All four fields are required. I treated Id, PostId, VoteTypeId, and CreationDate as mandatory. If any are missing, DuckDB raises an error at load time — which I think is the right behaviour. Silent failures are harder to debug than loud ones.
The outlier view should always reflect current data. That's why it's recreated on every run rather than created once and left.


## AI Tool Usage

Specific Use Cases:
I used AI help in a few specific areas. DuckDB has its own syntax for things like read_json_auto(), strftime(), and INSERT OR IGNORE that I wasn't fully familiar with, so I used AI to look those up and understand how they work. I also got help with test case preparation. Outside of the actual solution, I ran into some Windows-specific issues with Poetry that I used AI to help debug.
Percentage of Code Generated by AI:
The core decisions — how to handle deduplication, the ingestion strategy, how to implement the outlier formula, which week numbering to use — were all things I worked through myself. I'd estimate around 50% of the work involved AI, mainly for DuckDB syntax lookups, pytest patterns, and sorting out the poetry environment issues. Everything AI suggested was checked and tested before I used it.
How AI-Generated Code Was Reviewed:
I verified the outlier logic by hand — the sample data has 16 votes across 9 weeks, giving a mean of about 1.78. I checked each week's deviation manually and confirmed the output matched the README's expected table. The strftime('%W') choice was also verified against the sample before committing. For the test cases, I made sure each one was actually testing something meaningful rather than just bumping up coverage numbers.