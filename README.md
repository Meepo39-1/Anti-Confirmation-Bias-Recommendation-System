# Project description

This project presents a prototype of a recommendation system created with the goal in mind to alleviate the dangers of [confirmation bias](https://en.wikipedia.org/wiki/Confirmation_bias)
and [echo chambers](https://en.wikipedia.org/wiki/Echo_chamber_(media)) on internet.

## What is a recommendation system?

A recommendation system is an information filtering tool. The model searches for data related to the user's tastes and retrieves back the most relevant info for the user.

A great example of this technology is Youtube's recommendation alghoritm, that tries to show you, the user, relevant videos that you will like/share/comment to.

## What does your recommendation system...recommend?

Valid question. This recommender system will suggest posts from [r/changemyview](https://www.reddit.com/r/changemyview/) - a community where users create posts about different topics that they would like to change their opinion about, or at least see things trough a new perspective.

## How should I rate the recommendations?

Ratings represent a continous value ranging from -1 and 1. 

Your rating should reflect how much of a new perspective you were presented with:

>  **1** -> I'm mindblown! This post definetely changed my perspective on the topic presented/other tangent subjects / any topic discussed in the comment section
>
>  **0.5** -> This post presented some new perspectives about the topic presented / other tangent subjects / any topic discussed in the comment section
>  
>  **0** -> I'm not really sure
>  
>  **-0.5** -> Mostly, I haven't been exposed to any new perspective about the topic presented / other tangent subjects / any topic discussed in the comment section
>  
>  **-1** -> I'm bored. This post definetely didn't present any new perspective about the topic presented / other tangent subjects / any topic discussed in the comment section
>
Notes:
 * You can write any values( like 0.2,-0.7...etc) as long as it is between -1, and 1. Above there are just some intuitive explanations of what those numerical value are supposed to mean
 * You **don't** have to agree with the ideas presented in the post or comment section. Same for liking them. Even if they are blatanly false. All that matters is that your brain was challenged to see things in a new light.
 * In case it wasn't clear from the wording. The difference between a 0.5 and 1 rating isn't linear. Meaning that your standards for a 1 rating should be really high. Think that you need to be exposed to 3+ new ways of seeing things to approach such a rating. Same for the negative ratings.

## How can I test it?
If you're feeling brave you can clone this repo locally and follow the steps from "setup instructions.txt"
Otherwise, you can run these google colab links: [TO BE ADDED](), [TO BE ADDED]()