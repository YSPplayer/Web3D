#pragma once
#include "softmax.h"
#include <cmath>
namespace DeepLr::Neural {
	Tensor3D SoftMax::Forward(const Tensor3D& input) {
		Tensor3D result(1,10,4);//shape [4,10]
		int32_t h = result.Height();
		int32_t w = result.Width();
		for (int32_t y = 0; y < h; ++y) {
			float max = std::numeric_limits<float>::lowest();
			for (int32_t x = 0; x < w; ++x) {
				max = std::max(max, input.Get(0, y, x));
			}
			float sum = 0.0;
			for (int32_t x = 0; x < w; ++x) {
				sum += exp(input.Get(0,y,x) - max);
			}
			for (int32_t x = 0; x < w; ++x) {
				result.At(0, y, x) = exp(input.Get(0, y, x) - max) / sum;
			}
		}
		return result;
	}
}