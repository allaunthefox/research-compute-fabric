// PIST Shells: Concentric Polygonal Rings
// 3D slice of PIST pathological manifold

// Each shell k is a regular (2k+1)-gon with radius k
// Inner shells: dense, low curvature
// Outer shells: sparse, high curvature

// Shell k=0, capacity=1, radius=0mm
translate([0, 0, 0]) sphere(r=2, $fn=32);

// Shell k=1, capacity=3, radius=5mm
// Vertices at positions t=0..2
translate([5.00, 0.00, 2]) sphere(r=1.5, $fn=16);
translate([-2.50, 4.33, 2]) sphere(r=1.5, $fn=16);
translate([-2.50, -4.33, 2]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=1
linear_extrude(height=0.5, center=true) polygon(points=[[5.00, 0.00, 2], [-2.50, 4.33, 2], [-2.50, -4.33, 2]]);

// Shell k=2, capacity=5, radius=10mm
// Vertices at positions t=0..4
translate([10.00, 0.00, 4]) sphere(r=1.5, $fn=16);
translate([3.09, 9.51, 4]) sphere(r=1.5, $fn=16);
translate([-8.09, 5.88, 4]) sphere(r=1.5, $fn=16);
translate([-8.09, -5.88, 4]) sphere(r=1.5, $fn=16);
translate([3.09, -9.51, 4]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=2
linear_extrude(height=0.5, center=true) polygon(points=[[10.00, 0.00, 4], [3.09, 9.51, 4], [-8.09, 5.88, 4], [-8.09, -5.88, 4], [3.09, -9.51, 4]]);

// Shell k=3, capacity=7, radius=15mm
// Vertices at positions t=0..6
translate([15.00, 0.00, 6]) sphere(r=1.5, $fn=16);
translate([9.35, 11.73, 6]) sphere(r=1.5, $fn=16);
translate([-3.34, 14.62, 6]) sphere(r=1.5, $fn=16);
translate([-13.51, 6.51, 6]) sphere(r=1.5, $fn=16);
translate([-13.51, -6.51, 6]) sphere(r=1.5, $fn=16);
translate([-3.34, -14.62, 6]) sphere(r=1.5, $fn=16);
translate([9.35, -11.73, 6]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=3
linear_extrude(height=0.5, center=true) polygon(points=[[15.00, 0.00, 6], [9.35, 11.73, 6], [-3.34, 14.62, 6], [-13.51, 6.51, 6], [-13.51, -6.51, 6], [-3.34, -14.62, 6], [9.35, -11.73, 6]]);

// Shell k=4, capacity=9, radius=20mm
// Vertices at positions t=0..8
translate([20.00, 0.00, 8]) sphere(r=1.5, $fn=16);
translate([15.32, 12.86, 8]) sphere(r=1.5, $fn=16);
translate([3.47, 19.70, 8]) sphere(r=1.5, $fn=16);
translate([-10.00, 17.32, 8]) sphere(r=1.5, $fn=16);
translate([-18.79, 6.84, 8]) sphere(r=1.5, $fn=16);
translate([-18.79, -6.84, 8]) sphere(r=1.5, $fn=16);
translate([-10.00, -17.32, 8]) sphere(r=1.5, $fn=16);
translate([3.47, -19.70, 8]) sphere(r=1.5, $fn=16);
translate([15.32, -12.86, 8]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=4
linear_extrude(height=0.5, center=true) polygon(points=[[20.00, 0.00, 8], [15.32, 12.86, 8], [3.47, 19.70, 8], [-10.00, 17.32, 8], [-18.79, 6.84, 8], [-18.79, -6.84, 8], [-10.00, -17.32, 8], [3.47, -19.70, 8], [15.32, -12.86, 8]]);

// Shell k=5, capacity=11, radius=25mm
// Vertices at positions t=0..10
translate([25.00, 0.00, 10]) sphere(r=1.5, $fn=16);
translate([21.03, 13.52, 10]) sphere(r=1.5, $fn=16);
translate([10.39, 22.74, 10]) sphere(r=1.5, $fn=16);
translate([-3.56, 24.75, 10]) sphere(r=1.5, $fn=16);
translate([-16.37, 18.89, 10]) sphere(r=1.5, $fn=16);
translate([-23.99, 7.04, 10]) sphere(r=1.5, $fn=16);
translate([-23.99, -7.04, 10]) sphere(r=1.5, $fn=16);
translate([-16.37, -18.89, 10]) sphere(r=1.5, $fn=16);
translate([-3.56, -24.75, 10]) sphere(r=1.5, $fn=16);
translate([10.39, -22.74, 10]) sphere(r=1.5, $fn=16);
translate([21.03, -13.52, 10]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=5
linear_extrude(height=0.5, center=true) polygon(points=[[25.00, 0.00, 10], [21.03, 13.52, 10], [10.39, 22.74, 10], [-3.56, 24.75, 10], [-16.37, 18.89, 10], [-23.99, 7.04, 10], [-23.99, -7.04, 10], [-16.37, -18.89, 10], [-3.56, -24.75, 10], [10.39, -22.74, 10], [21.03, -13.52, 10]]);

// Shell k=6, capacity=13, radius=30mm
// Vertices at positions t=0..12
translate([30.00, 0.00, 12]) sphere(r=1.5, $fn=16);
translate([26.56, 13.94, 12]) sphere(r=1.5, $fn=16);
translate([17.04, 24.69, 12]) sphere(r=1.5, $fn=16);
translate([3.62, 29.78, 12]) sphere(r=1.5, $fn=16);
translate([-10.64, 28.05, 12]) sphere(r=1.5, $fn=16);
translate([-22.46, 19.89, 12]) sphere(r=1.5, $fn=16);
translate([-29.13, 7.18, 12]) sphere(r=1.5, $fn=16);
translate([-29.13, -7.18, 12]) sphere(r=1.5, $fn=16);
translate([-22.46, -19.89, 12]) sphere(r=1.5, $fn=16);
translate([-10.64, -28.05, 12]) sphere(r=1.5, $fn=16);
translate([3.62, -29.78, 12]) sphere(r=1.5, $fn=16);
translate([17.04, -24.69, 12]) sphere(r=1.5, $fn=16);
translate([26.56, -13.94, 12]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=6
linear_extrude(height=0.5, center=true) polygon(points=[[30.00, 0.00, 12], [26.56, 13.94, 12], [17.04, 24.69, 12], [3.62, 29.78, 12], [-10.64, 28.05, 12], [-22.46, 19.89, 12], [-29.13, 7.18, 12], [-29.13, -7.18, 12], [-22.46, -19.89, 12], [-10.64, -28.05, 12], [3.62, -29.78, 12], [17.04, -24.69, 12], [26.56, -13.94, 12]]);

// Shell k=7, capacity=15, radius=35mm
// Vertices at positions t=0..14
translate([35.00, 0.00, 14]) sphere(r=1.5, $fn=16);
translate([31.97, 14.24, 14]) sphere(r=1.5, $fn=16);
translate([23.42, 26.01, 14]) sphere(r=1.5, $fn=16);
translate([10.82, 33.29, 14]) sphere(r=1.5, $fn=16);
translate([-3.66, 34.81, 14]) sphere(r=1.5, $fn=16);
translate([-17.50, 30.31, 14]) sphere(r=1.5, $fn=16);
translate([-28.32, 20.57, 14]) sphere(r=1.5, $fn=16);
translate([-34.24, 7.28, 14]) sphere(r=1.5, $fn=16);
translate([-34.24, -7.28, 14]) sphere(r=1.5, $fn=16);
translate([-28.32, -20.57, 14]) sphere(r=1.5, $fn=16);
translate([-17.50, -30.31, 14]) sphere(r=1.5, $fn=16);
translate([-3.66, -34.81, 14]) sphere(r=1.5, $fn=16);
translate([10.82, -33.29, 14]) sphere(r=1.5, $fn=16);
translate([23.42, -26.01, 14]) sphere(r=1.5, $fn=16);
translate([31.97, -14.24, 14]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=7
linear_extrude(height=0.5, center=true) polygon(points=[[35.00, 0.00, 14], [31.97, 14.24, 14], [23.42, 26.01, 14], [10.82, 33.29, 14], [-3.66, 34.81, 14], [-17.50, 30.31, 14], [-28.32, 20.57, 14], [-34.24, 7.28, 14], [-34.24, -7.28, 14], [-28.32, -20.57, 14], [-17.50, -30.31, 14], [-3.66, -34.81, 14], [10.82, -33.29, 14], [23.42, -26.01, 14], [31.97, -14.24, 14]]);

// Shell k=8, capacity=17, radius=40mm
// Vertices at positions t=0..16
translate([40.00, 0.00, 16]) sphere(r=1.5, $fn=16);
translate([37.30, 14.45, 16]) sphere(r=1.5, $fn=16);
translate([29.56, 26.95, 16]) sphere(r=1.5, $fn=16);
translate([17.83, 35.81, 16]) sphere(r=1.5, $fn=16);
translate([3.69, 39.83, 16]) sphere(r=1.5, $fn=16);
translate([-10.95, 38.47, 16]) sphere(r=1.5, $fn=16);
translate([-24.11, 31.92, 16]) sphere(r=1.5, $fn=16);
translate([-34.01, 21.06, 16]) sphere(r=1.5, $fn=16);
translate([-39.32, 7.35, 16]) sphere(r=1.5, $fn=16);
translate([-39.32, -7.35, 16]) sphere(r=1.5, $fn=16);
translate([-34.01, -21.06, 16]) sphere(r=1.5, $fn=16);
translate([-24.11, -31.92, 16]) sphere(r=1.5, $fn=16);
translate([-10.95, -38.47, 16]) sphere(r=1.5, $fn=16);
translate([3.69, -39.83, 16]) sphere(r=1.5, $fn=16);
translate([17.83, -35.81, 16]) sphere(r=1.5, $fn=16);
translate([29.56, -26.95, 16]) sphere(r=1.5, $fn=16);
translate([37.30, -14.45, 16]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=8
linear_extrude(height=0.5, center=true) polygon(points=[[40.00, 0.00, 16], [37.30, 14.45, 16], [29.56, 26.95, 16], [17.83, 35.81, 16], [3.69, 39.83, 16], [-10.95, 38.47, 16], [-24.11, 31.92, 16], [-34.01, 21.06, 16], [-39.32, 7.35, 16], [-39.32, -7.35, 16], [-34.01, -21.06, 16], [-24.11, -31.92, 16], [-10.95, -38.47, 16], [3.69, -39.83, 16], [17.83, -35.81, 16], [29.56, -26.95, 16], [37.30, -14.45, 16]]);

// Shell k=9, capacity=19, radius=45mm
// Vertices at positions t=0..18
translate([45.00, 0.00, 18]) sphere(r=1.5, $fn=16);
translate([42.56, 14.61, 18]) sphere(r=1.5, $fn=16);
translate([35.51, 27.64, 18]) sphere(r=1.5, $fn=16);
translate([24.61, 37.67, 18]) sphere(r=1.5, $fn=16);
translate([11.05, 43.62, 18]) sphere(r=1.5, $fn=16);
translate([-3.72, 44.85, 18]) sphere(r=1.5, $fn=16);
translate([-18.08, 41.21, 18]) sphere(r=1.5, $fn=16);
translate([-30.48, 33.11, 18]) sphere(r=1.5, $fn=16);
translate([-39.58, 21.42, 18]) sphere(r=1.5, $fn=16);
translate([-44.39, 7.41, 18]) sphere(r=1.5, $fn=16);
translate([-44.39, -7.41, 18]) sphere(r=1.5, $fn=16);
translate([-39.58, -21.42, 18]) sphere(r=1.5, $fn=16);
translate([-30.48, -33.11, 18]) sphere(r=1.5, $fn=16);
translate([-18.08, -41.21, 18]) sphere(r=1.5, $fn=16);
translate([-3.72, -44.85, 18]) sphere(r=1.5, $fn=16);
translate([11.05, -43.62, 18]) sphere(r=1.5, $fn=16);
translate([24.61, -37.67, 18]) sphere(r=1.5, $fn=16);
translate([35.51, -27.64, 18]) sphere(r=1.5, $fn=16);
translate([42.56, -14.61, 18]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=9
linear_extrude(height=0.5, center=true) polygon(points=[[45.00, 0.00, 18], [42.56, 14.61, 18], [35.51, 27.64, 18], [24.61, 37.67, 18], [11.05, 43.62, 18], [-3.72, 44.85, 18], [-18.08, 41.21, 18], [-30.48, 33.11, 18], [-39.58, 21.42, 18], [-44.39, 7.41, 18], [-44.39, -7.41, 18], [-39.58, -21.42, 18], [-30.48, -33.11, 18], [-18.08, -41.21, 18], [-3.72, -44.85, 18], [11.05, -43.62, 18], [24.61, -37.67, 18], [35.51, -27.64, 18], [42.56, -14.61, 18]]);

// Shell k=10, capacity=21, radius=50mm
// Vertices at positions t=0..20
translate([50.00, 0.00, 20]) sphere(r=1.5, $fn=16);
translate([47.78, 14.74, 20]) sphere(r=1.5, $fn=16);
translate([41.31, 28.17, 20]) sphere(r=1.5, $fn=16);
translate([31.17, 39.09, 20]) sphere(r=1.5, $fn=16);
translate([18.27, 46.54, 20]) sphere(r=1.5, $fn=16);
translate([3.74, 49.86, 20]) sphere(r=1.5, $fn=16);
translate([-11.13, 48.75, 20]) sphere(r=1.5, $fn=16);
translate([-25.00, 43.30, 20]) sphere(r=1.5, $fn=16);
translate([-36.65, 34.01, 20]) sphere(r=1.5, $fn=16);
translate([-45.05, 21.69, 20]) sphere(r=1.5, $fn=16);
translate([-49.44, 7.45, 20]) sphere(r=1.5, $fn=16);
translate([-49.44, -7.45, 20]) sphere(r=1.5, $fn=16);
translate([-45.05, -21.69, 20]) sphere(r=1.5, $fn=16);
translate([-36.65, -34.01, 20]) sphere(r=1.5, $fn=16);
translate([-25.00, -43.30, 20]) sphere(r=1.5, $fn=16);
translate([-11.13, -48.75, 20]) sphere(r=1.5, $fn=16);
translate([3.74, -49.86, 20]) sphere(r=1.5, $fn=16);
translate([18.27, -46.54, 20]) sphere(r=1.5, $fn=16);
translate([31.17, -39.09, 20]) sphere(r=1.5, $fn=16);
translate([41.31, -28.17, 20]) sphere(r=1.5, $fn=16);
translate([47.78, -14.74, 20]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=10
linear_extrude(height=0.5, center=true) polygon(points=[[50.00, 0.00, 20], [47.78, 14.74, 20], [41.31, 28.17, 20], [31.17, 39.09, 20], [18.27, 46.54, 20], [3.74, 49.86, 20], [-11.13, 48.75, 20], [-25.00, 43.30, 20], [-36.65, 34.01, 20], [-45.05, 21.69, 20], [-49.44, 7.45, 20], [-49.44, -7.45, 20], [-45.05, -21.69, 20], [-36.65, -34.01, 20], [-25.00, -43.30, 20], [-11.13, -48.75, 20], [3.74, -49.86, 20], [18.27, -46.54, 20], [31.17, -39.09, 20], [41.31, -28.17, 20], [47.78, -14.74, 20]]);

// Shell k=11, capacity=23, radius=55mm
// Vertices at positions t=0..22
translate([55.00, 0.00, 22]) sphere(r=1.5, $fn=16);
translate([52.96, 14.84, 22]) sphere(r=1.5, $fn=16);
translate([46.99, 28.58, 22]) sphere(r=1.5, $fn=16);
translate([37.54, 40.20, 22]) sphere(r=1.5, $fn=16);
translate([25.30, 48.83, 22]) sphere(r=1.5, $fn=16);
translate([11.19, 53.85, 22]) sphere(r=1.5, $fn=16);
translate([-3.75, 54.87, 22]) sphere(r=1.5, $fn=16);
translate([-18.42, 51.82, 22]) sphere(r=1.5, $fn=16);
translate([-31.72, 44.93, 22]) sphere(r=1.5, $fn=16);
translate([-42.66, 34.71, 22]) sphere(r=1.5, $fn=16);
translate([-50.45, 21.91, 22]) sphere(r=1.5, $fn=16);
translate([-54.49, 7.49, 22]) sphere(r=1.5, $fn=16);
translate([-54.49, -7.49, 22]) sphere(r=1.5, $fn=16);
translate([-50.45, -21.91, 22]) sphere(r=1.5, $fn=16);
translate([-42.66, -34.71, 22]) sphere(r=1.5, $fn=16);
translate([-31.72, -44.93, 22]) sphere(r=1.5, $fn=16);
translate([-18.42, -51.82, 22]) sphere(r=1.5, $fn=16);
translate([-3.75, -54.87, 22]) sphere(r=1.5, $fn=16);
translate([11.19, -53.85, 22]) sphere(r=1.5, $fn=16);
translate([25.30, -48.83, 22]) sphere(r=1.5, $fn=16);
translate([37.54, -40.20, 22]) sphere(r=1.5, $fn=16);
translate([46.99, -28.58, 22]) sphere(r=1.5, $fn=16);
translate([52.96, -14.84, 22]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=11
linear_extrude(height=0.5, center=true) polygon(points=[[55.00, 0.00, 22], [52.96, 14.84, 22], [46.99, 28.58, 22], [37.54, 40.20, 22], [25.30, 48.83, 22], [11.19, 53.85, 22], [-3.75, 54.87, 22], [-18.42, 51.82, 22], [-31.72, 44.93, 22], [-42.66, 34.71, 22], [-50.45, 21.91, 22], [-54.49, 7.49, 22], [-54.49, -7.49, 22], [-50.45, -21.91, 22], [-42.66, -34.71, 22], [-31.72, -44.93, 22], [-18.42, -51.82, 22], [-3.75, -54.87, 22], [11.19, -53.85, 22], [25.30, -48.83, 22], [37.54, -40.20, 22], [46.99, -28.58, 22], [52.96, -14.84, 22]]);

// Shell k=12, capacity=25, radius=60mm
// Vertices at positions t=0..24
translate([60.00, 0.00, 24]) sphere(r=1.5, $fn=16);
translate([58.11, 14.92, 24]) sphere(r=1.5, $fn=16);
translate([52.58, 28.91, 24]) sphere(r=1.5, $fn=16);
translate([43.74, 41.07, 24]) sphere(r=1.5, $fn=16);
translate([32.15, 50.66, 24]) sphere(r=1.5, $fn=16);
translate([18.54, 57.06, 24]) sphere(r=1.5, $fn=16);
translate([3.77, 59.88, 24]) sphere(r=1.5, $fn=16);
translate([-11.24, 58.94, 24]) sphere(r=1.5, $fn=16);
translate([-25.55, 54.29, 24]) sphere(r=1.5, $fn=16);
translate([-38.25, 46.23, 24]) sphere(r=1.5, $fn=16);
translate([-48.54, 35.27, 24]) sphere(r=1.5, $fn=16);
translate([-55.79, 22.09, 24]) sphere(r=1.5, $fn=16);
translate([-59.53, 7.52, 24]) sphere(r=1.5, $fn=16);
translate([-59.53, -7.52, 24]) sphere(r=1.5, $fn=16);
translate([-55.79, -22.09, 24]) sphere(r=1.5, $fn=16);
translate([-48.54, -35.27, 24]) sphere(r=1.5, $fn=16);
translate([-38.25, -46.23, 24]) sphere(r=1.5, $fn=16);
translate([-25.55, -54.29, 24]) sphere(r=1.5, $fn=16);
translate([-11.24, -58.94, 24]) sphere(r=1.5, $fn=16);
translate([3.77, -59.88, 24]) sphere(r=1.5, $fn=16);
translate([18.54, -57.06, 24]) sphere(r=1.5, $fn=16);
translate([32.15, -50.66, 24]) sphere(r=1.5, $fn=16);
translate([43.74, -41.07, 24]) sphere(r=1.5, $fn=16);
translate([52.58, -28.91, 24]) sphere(r=1.5, $fn=16);
translate([58.11, -14.92, 24]) sphere(r=1.5, $fn=16);

// Polygon ring for shell k=12
linear_extrude(height=0.5, center=true) polygon(points=[[60.00, 0.00, 24], [58.11, 14.92, 24], [52.58, 28.91, 24], [43.74, 41.07, 24], [32.15, 50.66, 24], [18.54, 57.06, 24], [3.77, 59.88, 24], [-11.24, 58.94, 24], [-25.55, 54.29, 24], [-38.25, 46.23, 24], [-48.54, 35.27, 24], [-55.79, 22.09, 24], [-59.53, 7.52, 24], [-59.53, -7.52, 24], [-55.79, -22.09, 24], [-48.54, -35.27, 24], [-38.25, -46.23, 24], [-25.55, -54.29, 24], [-11.24, -58.94, 24], [3.77, -59.88, 24], [18.54, -57.06, 24], [32.15, -50.66, 24], [43.74, -41.07, 24], [52.58, -28.91, 24], [58.11, -14.92, 24]]);

// Mirror involution connections between shells
// Shell 1: mirror axis at t=1
color([1, 0, 0, 0.3]) translate([-2.50, 4.33, 2]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 2: mirror axis at t=2
color([1, 0, 0, 0.3]) translate([-8.09, 5.88, 4]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 3: mirror axis at t=3
color([1, 0, 0, 0.3]) translate([-13.51, 6.51, 6]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 4: mirror axis at t=4
color([1, 0, 0, 0.3]) translate([-18.79, 6.84, 8]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 5: mirror axis at t=5
color([1, 0, 0, 0.3]) translate([-23.99, 7.04, 10]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 6: mirror axis at t=6
color([1, 0, 0, 0.3]) translate([-29.13, 7.18, 12]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 7: mirror axis at t=7
color([1, 0, 0, 0.3]) translate([-34.24, 7.28, 14]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 8: mirror axis at t=8
color([1, 0, 0, 0.3]) translate([-39.32, 7.35, 16]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 9: mirror axis at t=9
color([1, 0, 0, 0.3]) translate([-44.39, 7.41, 18]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 10: mirror axis at t=10
color([1, 0, 0, 0.3]) translate([-49.44, 7.45, 20]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 11: mirror axis at t=11
color([1, 0, 0, 0.3]) translate([-54.49, 7.49, 22]) cylinder(h=5, r=0.5, center=true, $fn=8);
// Shell 12: mirror axis at t=12
color([1, 0, 0, 0.3]) translate([-59.53, 7.52, 24]) cylinder(h=5, r=0.5, center=true, $fn=8);
