#pragma once
#include "layer.h"
#include "../data.h"
#include <vector>
namespace DeepLr::Neural {
	class Conv2D :public Layer {
	public:
		Conv2D(int32_t ksize);
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output)override;

	private:
		std::vector<Kernel> kernels;//¾í»ýºË
		Tensor3D oldx;
		Tensor3D bias; //³¬²ÎÆ«ÖÃB
		Tensor3D dbias;//³¬²ÎÆ«ÖÃB Æ«µ¼ºó
	};
}