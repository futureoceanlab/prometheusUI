#include <cstdlib>
#include <cstdint>
#include <iostream>
#include <fstream>
#include <math.h>  // fmod
#include <iomanip>
#include <time.h>
#include <algorithm>

#include <png++/png.hpp>

#include "kcomptables.h"


#define ROW_SIZE        240
#define COL_SIZE        320
#define CAPTURE_SIZE    (COL_SIZE*ROW_SIZE)
#define FRAME_SIZE      (CAPTURE_SIZE*4)

#define BS_FREQ                    6
#define BS_INDEX_OF_REFRACTION     1.34
#define BS_WAVELENGTH              (300 / (BS_FREQ * 4.0 * BS_INDEX_OF_REFRACTION))


#define SAMPLE_IDX(x, y, capture)   ((CAPTURE_SIZE*capture) + (COL_SIZE*x) + y)


// #define TRACE_CALC 1


template <class T> uint32_t findRising(const T* const haystack, const uint32_t& haystack_len, const T& needle) {
    for (auto i = 0; i < haystack_len-1; ++i) {
        // std::cout << "findRising: i=" << i << "  needle=" << needle << "  haystack[i]=" << haystack[i] << std::endl;
        if (haystack[i] <= needle && haystack[i+1] > needle) {
            return i;
        }
    }

    // XXX: This probably indicates an error we should handle more explicitly.
    std::cout << "findRising reached end of table" << std::endl;
    return haystack_len-1;
}

template <class T> uint32_t findFalling(const T* const haystack, const uint32_t& haystack_len, const T& needle) {
    for (auto i = 0; i < haystack_len-1; ++i) {
        if (haystack[i] >= needle && haystack[i+1] < needle) {
            return i;
        }
    }

    // XXX: This probably indicates an error we should handle more explicitly.
    std::cout << "findFalling reached end of table" << std::endl;
    return haystack_len-1;
}

// Not in stdlib until C++17.
template<class T> const T& clamp( const T& v, const T& lo, const T& hi ) {
    if (v < lo) { return lo; }
    if (v > hi) { return hi; }
    return v;
}

template<class T> T table_lerp(const T* const table, const uint32_t& section, const T& fv) {
    auto slope = table[section+1] - table[section];
    auto est = (fv - table[section])/slope;
    auto phase = fmod((section + est) / BS_WAVELENGTH, 1.0);
    return phase;
}

int dcsInverse(const int16_t* const data, const uint32_t& x, const uint32_t& y, float* rval) {
    auto v0 = data[SAMPLE_IDX(x, y, 0)];
    auto v1 = data[SAMPLE_IDX(x, y, 1)];
    auto v2 = data[SAMPLE_IDX(x, y, 2)];
    auto v3 = data[SAMPLE_IDX(x, y, 3)];
        
#ifdef TRACE_CALC
    std::cout << "v[] = " << v0 << ", " << v1 << ", " << v2 << ", " << v3 << std::endl;
#endif

    if (v0 == 0 && v1 == 0) {
        // XXX: How should we handle this situation?
        std::cerr << "zeroes in input" << std::endl;
        *rval = -1.0;
        return 0;
    }

    float amplitude = float(abs(v0) + abs(v1));
    auto fv0n = float(v0) / amplitude;
    auto fv1n = float(v1) / amplitude;
    
#ifdef TRACE_CALC
    std::cout << "ampl=" << amplitude << " fv0n=" << fv0n << " fv1n=" << fv1n << std::endl;
#endif

    if (fv0n > DCITABLE_MAX) {
        
        std::cerr << "past max range" << std::endl;
        // @KK: Not clear to me why there's the offset by 1 in the Python version.  Should check that this is correct.
        // (I don't have any data that exercises this path.)
        auto section = findRising(normDCIconvshift, TABLE_SIZE, fv1n) - 1;
        *rval = table_lerp(normDCIconvshift, section, fv1n);
        
    } else if (fv0n < DCITABLE_MIN) {
        
        std::cerr << "past min range" << std::endl;
        // @KK: Not clear to me why there's the offset by 1 in the Python version.  Should check that this is correct.
        // (I don't have any data that exercises this path.)
        auto section = findFalling(normDCIconvshift, TABLE_SIZE, fv1n -1 );
        *rval = table_lerp(normDCIconvshift, section, fv1n);
        
    } else {

        auto riseIndex = findRising(normDCIconv, TABLE_SIZE, fv0n);
        auto fallIndex = findFalling(normDCIconv, TABLE_SIZE, fv0n);

#ifdef TRACE_CALC
        std::cout << "  riseIndex = " << riseIndex << std::endl;
        std::cout << "  fallIndex = " << fallIndex << std::endl;
#endif
        
        auto shiftRiseSegMin = std::min(normDCIconvshift[riseIndex], normDCIconvshift[riseIndex+1]); // Could be precomputed.
        auto shiftRiseSegMax = std::max(normDCIconvshift[riseIndex], normDCIconvshift[riseIndex+1]); // Could be precomputed.

        uint32_t section;
        if ((shiftRiseSegMin < fv1n < shiftRiseSegMax) || fv1n <= DCISHIFTTABLE_MIN) {
            section = riseIndex;
        } else {
            section = fallIndex;
        }
        
        *rval = table_lerp(normDCIconv, section, fv0n);
    }
    
    return 0;
}

int main(int argc, char** argv) {
    // Parse arguments.
    if (argc < 2 || argc > 3) {
        std::cerr << "usage: " << argv[0] << " <input-file> [output.png]" << std::endl;
        return -1;
    }
    const char* outputPath = "output.png";
    if (argc >= 2) {
        outputPath = argv[2];
    }

    // Open input.
    std::ifstream fin(argv[1], std::ios_base::binary);
    if (!fin.is_open()) {
        std::cerr << "failed to open file" << std::endl;
        return -1;
    }

    clock_t start = clock();
    
    // Read FRAME_SIZE samples (16 bytes each) in file order.
    auto raw_data = new int16_t[FRAME_SIZE];
    for (int i = 0; i < FRAME_SIZE; i++) {
        if (fin.eof()) {
            std::cerr << "premature end of file" << std::endl;
            return -4;
        }
        
        int16_t v;
        fin.read(reinterpret_cast<char*>(&v), 2);
        raw_data[i] = v;
    }
    
    fin.peek();
    if (!fin.eof()) {
        std::cerr << "warning: finished reading, but not at end of file; offset is " << fin.tellg() << std::endl;
    }
    
    // Compute the raw (floating-point) output by applying dcsInverse to each pixel.
    auto raw_out = new float[ROW_SIZE][COL_SIZE];
    for (int x = 0; x < ROW_SIZE; x++) {
        for (int y = 0; y < COL_SIZE; y++) {

            float vInv;
            if (dcsInverse(raw_data, x, y, &vInv)) {
                std::cerr << "error computing inverse" << std::endl;
                return -3;
            }
            raw_out[x][y] = vInv;
        }
    }
    
    // Write greyscale image.
    png::image<png::rgb_pixel> image(ROW_SIZE, COL_SIZE);
    for (auto y = 0; y < image.get_height(); ++y) {
        for (auto x = 0; x < image.get_width(); ++x) {
            
            auto rawOutVal = raw_out[x][y];
            auto normOutVal = (rawOutVal+ 1.0) / 2.0;
            uint8_t quantNormOutVal = uint8_t(clamp(int(normOutVal * 256.0), 0, 255));
            
            image[y][x] = png::rgb_pixel(quantNormOutVal, quantNormOutVal, quantNormOutVal);
        }
    }
    image.write(outputPath);

    // Timing.
    auto elapsed = ((double)(clock()-start))/CLOCKS_PER_SEC;
    std::cout << "elapsed: " << elapsed << std::endl;
}

