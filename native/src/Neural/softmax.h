#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class SoftMax : public Layer {
	public:
		SoftMax();
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output)override;
	};
}