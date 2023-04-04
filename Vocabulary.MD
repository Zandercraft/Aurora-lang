# Aurora Vocabulary
This file sets out the various terms used to describe the 

## Legend
`|` - or  
`*`- zero or more of the thing before it

## Main Vocabulary Table
*Organized by least priority to most priority.*
```
expr     : KEYWORD:set IDENTIFIER EQ expr
         : com-ex ((KEYWORD:AND|KEYWORD:OR) com-ex)*

com-expr : not com-ex
         : ar-ex ((EE|LT|GT|LTE|GTE) ar-ex)*

ar-expr  : term ((PLUS|MINUS) term)*

term     : factor ((MUL|DIV|POW) factor)*

factor   : (PLUS|MINUS) factor
         : power
       
power    : atom (POW factor)*

atom     : INT|FLOAT|IDENTIFIER
         : LPAREN expr RPAREN
```
