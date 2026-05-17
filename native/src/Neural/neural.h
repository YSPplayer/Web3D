#pragma once
#include "../data.h"
#include <vector>
#include <memory>
#include <random>
#include "layer.h"
#include "sample.h"
#include "loss.h"
namespace DeepLr::Neural {
	class Neural {
	public:
		Neural(const std::vector<NeuralBuild> & builds);
		static std::shared_ptr<Neural> BuildDefaultNeural();
		void Train(std::vector<std::shared_ptr<Sample>>& samples, int32_t maxEpoch);
	private:
		std::vector<Layer*> neural;
		Loss loss;
		float TrainBatch(const std::vector<std::shared_ptr<Sample>>& samples,float lr);
		static std::shared_ptr<std::mt19937> g;
	};
}