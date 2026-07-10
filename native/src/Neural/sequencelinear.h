#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class SequenceLinear : public Layer {
	public:
		SequenceLinear();
		void SetShape(const TensorShape& lastshape, const TensorShape& shape) override;
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) override;
		void Update(float lr, int32_t batchSize) override;
		void ClearGrad() override;
		void AccumulateGrad(const Layer& other) override;
		Tensor3D GetW() const;
		Tensor3D GetB() const;
		void SetW(const Tensor3D& w);
		void SetB(const Tensor3D& b);
	private:
		Tensor3D w;
		Tensor3D b;
		Tensor3D dw;
		Tensor3D db;
		Tensor3D oldx;
		int32_t inputSize;
		int32_t outputSize;
	};
}
