package Inherit {
    private import ScalarValues::Integer;
    part def Rated {
        attribute cycles : Integer = 100000;
        constraint <'CON-1'> durable { cycles >= 100000 }
    }
    part <'PC-1'> weak : Rated {
        attribute redefines cycles = 90000;
    }
    part <'PC-2'> fine :> weak {
        attribute redefines cycles = 120000;
    }
    part <'PC-3'> own : Rated {
        constraint redefines durable { cycles >= 50000 }
        attribute redefines cycles = 60000;
    }
}
