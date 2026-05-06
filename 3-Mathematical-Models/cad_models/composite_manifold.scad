// Composite Pathological Manifold: 3D Slice
// 3D slice of PIST pathological manifold

// NOT the full 9D structure — a visualizable 3D projection
// Shows how PIST shells nest within sponge nodes on the horn

// The composite structure:
// - Gabriel's horn: backbone (x-axis curve)
// - Menger sponge nodes: attached at 8 sample points
// - PIST shells: inside each sponge node

module sponge_node(x_pos, horn_radius) {
  // Small Menger-like cube cluster at this horn position
  translate([x_pos, 0, 0]) {
    translate([-3, -3, -3]) cube([4, 4, 4], center=true); // subcube 0
    translate([-3, -3, 3]) cube([4, 4, 4], center=true); // subcube 1
    translate([-3, 3, -3]) cube([4, 4, 4], center=true); // subcube 2
    translate([-3, 3, 3]) cube([4, 4, 4], center=true); // subcube 3
    translate([3, -3, -3]) cube([4, 4, 4], center=true); // subcube 4
    translate([3, -3, 3]) cube([4, 4, 4], center=true); // subcube 5
    translate([3, 3, -3]) cube([4, 4, 4], center=true); // subcube 6
    translate([3, 3, 3]) cube([4, 4, 4], center=true); // subcube 7
  }
}

// Horn backbone
color([0.2, 0.2, 0.4]) {
  hull() {
    translate([3.2, 0, 0]) sphere(r=1.2, $fn=16);
    translate([6.4, 0, 0]) sphere(r=0.6, $fn=16);
  }
  hull() {
    translate([6.4, 0, 0]) sphere(r=0.6, $fn=16);
    translate([12.8, 0, 0]) sphere(r=0.3, $fn=16);
  }
  hull() {
    translate([12.8, 0, 0]) sphere(r=0.3, $fn=16);
    translate([25.6, 0, 0]) sphere(r=0.2, $fn=16);
  }
  hull() {
    translate([25.6, 0, 0]) sphere(r=0.2, $fn=16);
    translate([38.4, 0, 0]) sphere(r=0.1, $fn=16);
  }
  hull() {
    translate([38.4, 0, 0]) sphere(r=0.1, $fn=16);
    translate([48.0, 0, 0]) sphere(r=0.1, $fn=16);
  }
}

// Sponge nodes at sample positions
color([0.8, 0.4, 0.1]) {
  sponge_node(3.2, 1.2); // n=16
  sponge_node(6.4, 0.6); // n=32
  sponge_node(12.8, 0.3); // n=64
  sponge_node(25.6, 0.2); // n=128
  sponge_node(38.4, 0.1); // n=192
  sponge_node(48.0, 0.1); // n=240
}

// PIST shell inside sponge node 0 (n=16, k=4)
color([0.1, 0.7, 0.3]) translate([3.2, 0, 0]) {
  translate([6.0, 0.0, 0]) sphere(r=0.5, $fn=8); // t=0
  translate([4.6, 3.9, 0]) sphere(r=0.5, $fn=8); // t=1
  translate([1.0, 5.9, 0]) sphere(r=0.5, $fn=8); // t=2
  translate([-3.0, 5.2, 0]) sphere(r=0.5, $fn=8); // t=3
  translate([-5.6, 2.1, 0]) sphere(r=0.5, $fn=8); // t=4
  translate([-5.6, -2.1, 0]) sphere(r=0.5, $fn=8); // t=5
  translate([-3.0, -5.2, 0]) sphere(r=0.5, $fn=8); // t=6
  translate([1.0, -5.9, 0]) sphere(r=0.5, $fn=8); // t=7
  translate([4.6, -3.9, 0]) sphere(r=0.5, $fn=8); // t=8
}
