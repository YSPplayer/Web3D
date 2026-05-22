#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class FeatureToSequence : public Layer {
	public:
		FeatureToSequence();
		Tensor3D Forward(const Tensor3D& input) override;
		//void Update(float lr, int32_t batchSize) override {};
	};
}