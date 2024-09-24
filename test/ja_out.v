/* Generated by Yosys 0.44 (git sha1 80ba43d26, clang++ 15.0.0 -fPIC -O3) */

(* hdlname = "jfulladder" *)
(* top =  1  *)
(* src = "test2.v:1.1-8.10" *)
module jfulladder(y, carryout, a, b, carryin);
  wire _00_;
  wire _01_;
  wire _02_;
  wire _03_;
  wire _04_;
  wire _05_;
  wire _06_;
  wire _07_;
  wire _08_;
  wire _09_;
  wire _10_;
  wire _11_;
  (* src = "test2.v:3.9-3.10" *)
  input a;
  wire a;
  (* src = "test2.v:3.11-3.12" *)
  input b;
  wire b;
  (* src = "test2.v:3.13-3.20" *)
  input carryin;
  wire carryin;
  (* src = "test2.v:2.12-2.20" *)
  output carryout;
  wire carryout;
  (* src = "test2.v:2.10-2.11" *)
  output y;
  wire y;
  NOT _12_ (
    .A(b),
    .Y(_08_)
  );
  NOT _13_ (
    .A(a),
    .Y(_09_)
  );
  NOT _14_ (
    .A(carryin),
    .Y(_10_)
  );
  NOR _15_ (
    .A(b),
    .B(carryin),
    .Y(_11_)
  );
  NAND _16_ (
    .A(_08_),
    .B(_10_),
    .Y(_00_)
  );
  NAND _17_ (
    .A(b),
    .B(carryin),
    .Y(_01_)
  );
  NOT _18_ (
    .A(_01_),
    .Y(_02_)
  );
  NOR _19_ (
    .A(_11_),
    .B(_02_),
    .Y(_03_)
  );
  NAND _20_ (
    .A(_00_),
    .B(_01_),
    .Y(_04_)
  );
  NAND _21_ (
    .A(a),
    .B(_04_),
    .Y(_05_)
  );
  NAND _22_ (
    .A(_09_),
    .B(_03_),
    .Y(_06_)
  );
  NAND _23_ (
    .A(_05_),
    .B(_06_),
    .Y(y)
  );
  NAND _24_ (
    .A(a),
    .B(_00_),
    .Y(_07_)
  );
  NAND _25_ (
    .A(_01_),
    .B(_07_),
    .Y(carryout)
  );
endmodule