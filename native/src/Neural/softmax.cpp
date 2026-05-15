#pragma once
#include "softmax.h"
#include <cmath>
namespace DeepLr::Neural {
	SoftMax::SoftMax() {
		ntype = NeuralType::SoftMax;
	}
	Tensor3D SoftMax::Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) {
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
	Tensor3D SoftMax::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) { // [4,10]
		Tensor3D result(1, output.Width(), output.Height());
		for (int32_t y = 0; y < output.Height(); ++y) {
			const std::array<float, 10>& array = ToOneHot(target[y]);
			for (int32_t x = 0; x < output.Width(); ++x) {
				result.At(0, y, x) = (output.Get(0, y, x) - array[x]) / output.Height();
			}
			
		}
		return result;
	}
}