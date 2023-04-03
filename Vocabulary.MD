# Aurora Vocabulary
This file sets out the various terms used to describe the 

## Legend
`|` - or  
`*`- zero or more of the thing before it

## Main Vocabulary Table
```
expr   : term ((PLUS|MINUS) term)*

term   : factor ((MUL|DIV) factor)*

factor : INT | FLOAT
       : (PLUS|MINUS) factor
       : LPAREN expr RPAREN
```
