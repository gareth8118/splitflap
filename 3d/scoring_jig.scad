/*
   Copyright 2020 Scott Bezek and the splitflap contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

include<flap_dimensions.scad>

print_tolerance = 0.1;
jig_thickness = 2.0;
jig_border = 8.0;

ruler_width = 24.9;
ruler_depth = 1.6;

union() {
    // Jig base
    linear_extrude(height=jig_thickness) {

    }
    // card guide
    // ruler backstop

}

