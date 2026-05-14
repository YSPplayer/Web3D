#include "neural.h"
#include "conv2d.h"
#include "relu.h"
#include "maxpool.h"
#include "flatten.h"
#include "linear.h"
#include "softmax.h"
namespace DeepLr::Neural {
	Neural::Neural(const std::vector<NeuralBuild>& builds) {
		neural.resize(builds.size());
		for (int32_t i = 0; i < builds.size(); ++i) {
			auto& build = builds[i];
			neural[i] = nullptr;
			if (build.type == NeuralType::Conv2D) neural[i] = new Conv2D(build.c);
			else if(build.type == NeuralType::RelU)neural[i] = new Relu();
			else if (build.type == NeuralType::MaxPool)neural[i] = new MaxPool();
			else if (build.type == NeuralType::Flatten)neural[i] = new Flatten();
			else if (build.type == NeuralType::Linear)neural[i] = new Linear();
			else if (build.type == NeuralType::SoftMax)neural[i] = new SoftMax();
		}
	}
	void Neural::BuildNeural() {
		Neural* n = new Neural({ 
			NeuralBuild(NeuralType::Conv2D, 8),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::MaxPool),
			NeuralBuild(NeuralType::Conv2D,16),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::MaxPool),
			NeuralBuild(NeuralType::Conv2D,24),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::MaxPool),
			NeuralBuild(NeuralType::Conv2D,32),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::MaxPool),
			NeuralBuild(NeuralType::Flatten),
			NeuralBuild(NeuralType::Linear,64),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::Linear,40),
			NeuralBuild(NeuralType::SoftMax),
		});
	}
}