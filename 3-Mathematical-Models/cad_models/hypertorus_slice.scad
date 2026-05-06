// Hypertorus: 3D Slice of 4D Structure
// 3D slice of PIST pathological manifold

// Full hypertorus has 3 angular coordinates
// This model shows a 3D slice: theta, phi, with R=3, r=1
// The psi angle is represented by color/phase

// Major radius R = 30.0mm, minor radius r = 10.0mm
// Points colored by psi angle (the third, unseen dimension)

module torus_point(theta, phi, psi, R, r) {
  x = (R + r * cos(phi)) * cos(theta);
  y = (R + r * cos(phi)) * sin(theta);
  z = r * sin(phi);
  // Color by psi: [red=sin(psi), green=cos(psi), blue=0.5]
  color([0.5 + 0.5*sin(psi), 0.5 + 0.5*cos(psi), 0.5])
    translate([x, y, z]) sphere(r=1.5, $fn=8);
}

// Sample points using irrational rotations by PHI
torus_point(0.0000, 0.0000, 0.0000, 30.0, 10.0);
torus_point(1.6180, 2.6180, 4.2361, 30.0, 10.0);
torus_point(3.2361, 5.2361, 2.1890, 30.0, 10.0);
torus_point(4.8541, 1.5709, 0.1418, 30.0, 10.0);
torus_point(0.1890, 4.1890, 4.3779, 30.0, 10.0);
torus_point(1.8070, 0.5238, 2.3308, 30.0, 10.0);
torus_point(3.4250, 3.1418, 0.2837, 30.0, 10.0);
torus_point(5.0431, 5.7599, 4.5197, 30.0, 10.0);
torus_point(0.3779, 2.0947, 2.4726, 30.0, 10.0);
torus_point(1.9959, 4.7127, 0.4255, 30.0, 10.0);
torus_point(3.6140, 1.0476, 4.6616, 30.0, 10.0);
torus_point(5.2320, 3.6656, 2.6145, 30.0, 10.0);
torus_point(0.5669, 0.0005, 0.5673, 30.0, 10.0);
torus_point(2.1849, 2.6185, 4.8034, 30.0, 10.0);
torus_point(3.8029, 5.2365, 2.7563, 30.0, 10.0);
torus_point(5.4210, 1.5714, 0.7092, 30.0, 10.0);
torus_point(0.7558, 4.1894, 4.9452, 30.0, 10.0);
torus_point(2.3738, 0.5243, 2.8981, 30.0, 10.0);
torus_point(3.9919, 3.1423, 0.8510, 30.0, 10.0);
torus_point(5.6099, 5.7603, 5.0871, 30.0, 10.0);
torus_point(0.9448, 2.0952, 3.0400, 30.0, 10.0);
torus_point(2.5628, 4.7132, 0.9928, 30.0, 10.0);
torus_point(4.1808, 1.0481, 5.2289, 30.0, 10.0);
torus_point(5.7989, 3.6661, 3.1818, 30.0, 10.0);
torus_point(1.1337, 0.0010, 1.1347, 30.0, 10.0);
torus_point(2.7517, 2.6190, 5.3707, 30.0, 10.0);
torus_point(4.3698, 5.2370, 3.3236, 30.0, 10.0);
torus_point(5.9878, 1.5719, 1.2765, 30.0, 10.0);
torus_point(1.3227, 4.1899, 5.5126, 30.0, 10.0);
torus_point(2.9407, 0.5248, 3.4655, 30.0, 10.0);
torus_point(4.5587, 3.1428, 1.4183, 30.0, 10.0);
torus_point(6.1768, 5.7608, 5.6544, 30.0, 10.0);
torus_point(1.5116, 2.0957, 3.6073, 30.0, 10.0);
torus_point(3.1296, 4.7137, 1.5602, 30.0, 10.0);
torus_point(4.7477, 1.0486, 5.7962, 30.0, 10.0);
torus_point(0.0825, 3.6666, 3.7491, 30.0, 10.0);
torus_point(1.7006, 0.0014, 1.7020, 30.0, 10.0);
torus_point(3.3186, 2.6195, 5.9381, 30.0, 10.0);
torus_point(4.9366, 5.2375, 3.8910, 30.0, 10.0);
torus_point(0.2715, 1.5724, 1.8438, 30.0, 10.0);
torus_point(1.8895, 4.1904, 6.0799, 30.0, 10.0);
torus_point(3.5075, 0.5252, 4.0328, 30.0, 10.0);
torus_point(5.1256, 3.1433, 1.9857, 30.0, 10.0);
torus_point(0.4604, 5.7613, 6.2217, 30.0, 10.0);
torus_point(2.0785, 2.0962, 4.1746, 30.0, 10.0);
torus_point(3.6965, 4.7142, 2.1275, 30.0, 10.0);
torus_point(5.3145, 1.0490, 0.0804, 30.0, 10.0);
torus_point(0.6494, 3.6671, 4.3165, 30.0, 10.0);
torus_point(2.2674, 0.0019, 2.2693, 30.0, 10.0);
torus_point(3.8854, 2.6200, 0.2222, 30.0, 10.0);
torus_point(5.5035, 5.2380, 4.4583, 30.0, 10.0);
torus_point(0.8383, 1.5728, 2.4112, 30.0, 10.0);
torus_point(2.4564, 4.1909, 0.3640, 30.0, 10.0);
torus_point(4.0744, 0.5257, 4.6001, 30.0, 10.0);
torus_point(5.6924, 3.1438, 2.5530, 30.0, 10.0);
torus_point(1.0273, 5.7618, 0.5059, 30.0, 10.0);
torus_point(2.6453, 2.0966, 4.7420, 30.0, 10.0);
torus_point(4.2633, 4.7147, 2.6948, 30.0, 10.0);
torus_point(5.8814, 1.0495, 0.6477, 30.0, 10.0);
torus_point(1.2162, 3.6676, 4.8838, 30.0, 10.0);
torus_point(2.8343, 0.0024, 2.8367, 30.0, 10.0);
torus_point(4.4523, 2.6204, 0.7895, 30.0, 10.0);
torus_point(6.0703, 5.2385, 5.0256, 30.0, 10.0);
torus_point(1.4052, 1.5733, 2.9785, 30.0, 10.0);

// Torus skeleton (major circle)
color([0.3, 0.3, 0.3]) rotate_extrude($fn=64) translate([30.0, 0, 0]) circle(r=10.0, $fn=32);
