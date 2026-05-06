// Menger Sponge: Recursive Cube Removal
// 3D slice of PIST pathological manifold

// Iteration 0: solid cube
// Iteration 1: 20 subcubes (remove center + 6 face centers)
// Iteration 2: 400 subcubes
// Iteration 3: 8000 subcubes (visualized as simplified)

// Level 3 Menger sponge (simplified for visibility)
module sponge_cube(x, y, z, s) {
  translate([x, y, z]) cube([s, s, s], center=true);
}

// Level 2 sponge with subcube indices labeled
difference() {
  cube([90, 90, 90], center=true);
  translate([30, 0, 0]) cube([30.1, 30.1, 30.1], center=true);
  translate([-30, 0, 0]) cube([30.1, 30.1, 30.1], center=true);
  translate([0, 30, 0]) cube([30.1, 30.1, 30.1], center=true);
  translate([0, -30, 0]) cube([30.1, 30.1, 30.1], center=true);
  translate([0, 0, 30]) cube([30.1, 30.1, 30.1], center=true);
  translate([0, 0, -30]) cube([30.1, 30.1, 30.1], center=true);
  translate([0, 0, 0]) cube([30.1, 30.1, 30.1], center=true);
}

// Valid subcubes (remaining after removal)
color([0.2, 0.6, 0.9]) {
  translate([-30, -30, -30]) cube([28, 28, 28], center=true); // subcube 0
  translate([-30, -30, 0]) cube([28, 28, 28], center=true); // subcube 1
  translate([-30, -30, 30]) cube([28, 28, 28], center=true); // subcube 2
  translate([-30, 0, -30]) cube([28, 28, 28], center=true); // subcube 3
  translate([-30, 0, 30]) cube([28, 28, 28], center=true); // subcube 4
  translate([-30, 30, -30]) cube([28, 28, 28], center=true); // subcube 5
  translate([-30, 30, 0]) cube([28, 28, 28], center=true); // subcube 6
  translate([-30, 30, 30]) cube([28, 28, 28], center=true); // subcube 7
  translate([0, -30, -30]) cube([28, 28, 28], center=true); // subcube 8
  translate([0, -30, 30]) cube([28, 28, 28], center=true); // subcube 9
  translate([0, 30, -30]) cube([28, 28, 28], center=true); // subcube 10
  translate([0, 30, 30]) cube([28, 28, 28], center=true); // subcube 11
  translate([30, -30, -30]) cube([28, 28, 28], center=true); // subcube 12
  translate([30, -30, 0]) cube([28, 28, 28], center=true); // subcube 13
  translate([30, -30, 30]) cube([28, 28, 28], center=true); // subcube 14
  translate([30, 0, -30]) cube([28, 28, 28], center=true); // subcube 15
  translate([30, 0, 30]) cube([28, 28, 28], center=true); // subcube 16
  translate([30, 30, -30]) cube([28, 28, 28], center=true); // subcube 17
  translate([30, 30, 0]) cube([28, 28, 28], center=true); // subcube 18
  translate([30, 30, 30]) cube([28, 28, 28], center=true); // subcube 19
}
