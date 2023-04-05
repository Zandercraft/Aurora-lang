# Aurora Vocabulary
This file sets out the various terms used to describe the 

## Legend
`|` - or  
`*`- zero or more of the thing before it  
`?` - optional  

## Main Vocabulary Table
*Organized by least priority to most priority.*
```
expr       : KEYWORD:set IDENTIFIER EQ expr
           : com-ex ((KEYWORD:AND|KEYWORD:OR) com-ex)*

com-expr   : not com-ex
           : ar-ex ((EE|LT|GT|LTE|GTE) ar-ex)*

ar-expr    : term ((PLUS|MINUS) term)*

term       : factor ((MUL|DIV|POW) factor)*

factor     : (PLUS|MINUS) factor
           : power
       
power      : call (POW factor)*

call       : atom (LPAREN (expr (COMMA expr)*)? RPAREN)?

atom       : INT|FLOAT|IDENTIFIER
           : LPAREN expr RPAREN
           : for-expr
           : while-expr
           : fun-def
         
if-expr    : KEYWORD:if expr KEYWORD:then expr
             (KEYWORD:eli expr KEYWORD:then expr)?*
             (KEYWORD:el expr)?
           
for-expr   : KEYWORD:for IDENTIFIER EQ expr KEYWORD:TO expr
              (KEYWORD:step expr)? KEYWORD:then expr

while-expr : KEYWORD:while expr KEYWORD then expr

fun-def    : KEYWORD:fun IDENTIFIER?
              LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN
              ARROW expr
```
