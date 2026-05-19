#pragma once
#include "layer.h"
#include "../data.h"
#include <vector>
namespace DeepLr::Neural {
	class Conv2D :public Layer {
	public:
		Conv2D();
		void SetShape(const TensorShape& lastshape, const TensorShape& shape) override;
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target)override;
		void Update(float lr, int32_t batchSize) override;
		void SetKernels(const std::vector<Tensor3D>& kernels);
		inline std::vector<Tensor3D> GetKernels() {
			return kernels;
		}
		inline Tensor3D GetBias() {
			return bias;
		}
		void SetBias(const Tensor3D& bias);
	private:
		std::vector<Tensor3D> kernels;//¾í»ýºË
		std::vector<Tensor3D> dkernels;//·´¾í»ýºË
		//std::vector<Kernel> kernels;//¾í»ýºË
		Tensor3D oldx;
		Tensor3D bias; //³¬²ÎÆ«ÖÃB
		Tensor3D dbias;//³¬²ÎÆ«ÖÃB Æ«µ¼ºó
	};
}