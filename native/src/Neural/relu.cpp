#include <algorithm>
#include "relu.h"
namespace DeepLr::Neural {
	Relu::Relu() {
		ntype = NeuralType::RelU;
	}
	Tensor3D Relu::Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) {
		oldx = input;
		Tensor3D tensor3D(input.Channel(), input.Width(), input.Height());
		for (int32_t i = 0; i < tensor3D.Count(); ++i) {
			tensor3D.At(i) = std::max(0.0f, input.Get(i));
		}
		return tensor3D;
	}
	Tensor3D Relu::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
		Tensor3D tensor3D(output.Channel(), output.Width(), output.Height());
		for (int32_t i = 0; i < tensor3D.Count(); ++i) {
			tensor3D.At(i) = oldx.At(i) > 0.0f ? output.At(i) : 0.0f;
		}
		return tensor3D;
	}
}
