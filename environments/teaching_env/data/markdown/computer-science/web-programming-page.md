The Missing Link: An Introduction to Web Development and Programming

Chapter 32

we can round out our answer to match. PHP already provides us with a rounding function
called round, so we will use that to refine our response:

function tip($billTotal, $percent=.15){

$tip = $billTotal * $percent;
$roundedTip = round($tip, 2);
return $roundedTip;

}

Lastly we will combine our statements, as we did before, to eliminate extra variables and

shorten our code:

function tip($billTotal, $percent=.15){ return
round(($billTotal * $percent),2) }

Now we have a concise function that can perform a single task and perform it well. We
can refer to it anywhere in our page as often as we need to without having to copy and
paste the code. In fact, this is the perfect time to introduce a set of functions that allow us
to import other files into our page.

ADDITIONAL NOTES

Order helps! If all of your optional variables are at the end (right hand side) of the
definition, you will not have to pass empty quotes as place holders if you only

want to send the required variables.

The functions include(), require(), and require_once() all allow us to pass a file location
on our server that we want to use as part of our code. By importing these outside files, we
can  create  libraries  of  functions  or  class  files  and  insert  them  into  any  page  we  want  to
use them on. Each of these functions runs the same way, by passing a file location. If the
contents of the file are not critical to your page, you may want to only use include, as it
will not generate an error if the file is missing. Errors will be thrown by using require() or
require_once(). The former will always insert the contents of the file, while the latter will
only load the file if its contents are not already available. Using required_once() will save
us from redefinition errors caused by redefining functions or classes we already have. If the
contents of the file tip.php was our function, we could reference it in any page like this:

<?php
require_once("tip.php");
echo tip(49.99);
?>

Keywords, search terms: Functions, function scope

Tizag’s function review: http://www.tizag.com/phpT/phpfunctions.php

Helper Functions : http://net.tutsplus.com/tutorials/php/increase-productivity-by-creating-

php-helper-functions/

LEARN MORE

190
